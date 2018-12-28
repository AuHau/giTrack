import click
import git

from . import helpers, config as config_module


# TODO: [?] Offline mode
# TODO: Status in shell's prompt
# TODO: Concurrently running tracking? Per repo? Per account? Per provider?
# TODO: Automatic pausing using file activities (watchdog)
# TODO: Exception handling

def entrypoint(args, obj=None):
    """
    CLI entry point, where exceptions are handled.
    """
    cli(args, obj=obj or {})


@click.group()
@click.pass_context
def cli(ctx):
    repo_dir = helpers.get_repo_dir()
    ctx.obj['repo_dir'] = repo_dir

    if ctx.invoked_subcommand != 'init':
        ctx.obj['config'] = config_module.Config(repo_dir)

        provider_class = ctx.obj['config'].provider.klass()
        ctx.obj['provider'] = provider_class(ctx.obj['config'])


@cli.resultcallback()
def save_store(*args):
    ctx = click.get_current_context()

    if ctx.obj.get('config'):
        ctx.obj['config'].store.save()


@cli.command(short_help='Starts time tracking')
@click.pass_context
def start(ctx):
    if not ctx.obj['config'].store['running']:
        ctx.obj['provider'].start()
        ctx.obj['config'].store['running'] = True


@cli.command(short_help='Stops time tracking')
@click.option('--description', '-d', help='Description for the running time entry')
@click.pass_context
def stop(ctx, description):
    if ctx.obj['config'].store['running']:
        ctx.obj['provider'].stop(description)
        ctx.obj['config'].store['running'] = False


@cli.command(short_help='Initialize Git repo for time tracking')
@click.option('--check', is_flag=True, help='Instead of initializing the repo, checks whether it has '
                                            'been initialized before. If not exits the command with status code 2')
@click.option('--install-hook', is_flag=True, help='If you want to just install hook without initialization.')
@click.option('--no-hook', is_flag=True, help='If you want to skip Git\'s hook installation. You will be responsible to'
                                              ' set properly the hook to call \'gitrack hooks post-commit\'.'
                                              ' Without that giTrack won\'t function properly.')
@click.option('--config-destination', '-c', type=click.Choice(['local', 'store']),
              default='local',
              help='Specifies where to store the configuration for the initialized repository. '
                   '\'local\' means file in the root of the Git repository. '
                   '\'store\' means giTrack\'s internal storage. Default: local')
@click.pass_context
def init(ctx, check, install_hook, no_hook, config_destination):
    repo_dir = ctx.obj['repo_dir']

    if check:
        if helpers.is_repo_initialized(repo_dir):
            return
        else:
            exit(2)
    else:
        if install_hook:
            helpers.install_hook(repo_dir)
        else:
            helpers.init(repo_dir, config_module.ConfigDestination(config_destination), should_install_hook=not no_hook)


@cli.group(short_help='Git hooks invocations')
@click.pass_context
def hooks(ctx):
    pass


@hooks.command('post-commit', short_help='Post-commit git hook')
@click.pass_context
def hooks_post_commit(ctx):
    config = ctx.obj['config']
    if not config.store['running']:
        return

    provider = ctx.obj['provider']
    repo = git.Repo(ctx.obj['repo_dir'])
    commit = repo.head.commit
    message = commit.message.strip()

    task = project = None
    if config.tasks_support:
        task = helpers.get_task(config, repo)

    if config.project_support:
        try:
            project = int(config.project)
        except ValueError:
            project = config.project

    provider.stop(message, task=task, project=project)
    provider.start()
