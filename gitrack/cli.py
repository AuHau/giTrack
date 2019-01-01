from datetime import datetime

import click
import git

from gitrack import helpers, prompt, config as config_module, __version__

# Ideas for future
# TODO: [?] Offline mode
# TODO: Concurrently running tracking? Per repo? Per account? Per provider?
# TODO: Automatic pausing using file activities (watchdog)
# TODO: Exception handling
# TODO: Verbose & Debugs modes ==> silence warnings from Toggl


#################################################################
# Custom classes for Click


class Mutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")

        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs["help"] = (kwargs.get("help", "") + "Option is mutually exclusive with " + ", ".join(self.not_required_if) + ".").strip()
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts:
                if current_opt:
                    raise click.UsageError("Illegal usage: '" + str(self.name) + "' is mutually exclusive with " + str(mutex_opt) + ".")
                else:
                    self.prompt = None
        return super().handle_parse_result(ctx, opts, args)


def entrypoint(args, obj=None):
    """
    CLI entry point, where exceptions are handled.
    """
    cli(args, obj=obj or {})


@click.group()
@click.option('--quiet', '-q', is_flag=True, help="Don't print anything")
@click.version_option(__version__)
@click.pass_context
def cli(ctx, quiet):
    repo_dir = helpers.get_repo_dir()
    ctx.obj['repo_dir'] = repo_dir

    if quiet:
        # TODO: [Q] Is this good idea?
        click.echo = lambda *args, **kwargs: None

    if ctx.invoked_subcommand != 'init':
        ctx.obj['config'] = config_module.Config(repo_dir)

        provider_class = ctx.obj['config'].provider.klass()
        ctx.obj['provider'] = provider_class(ctx.obj['config'])


@cli.resultcallback()
def save_store(*args, **kwargs):
    ctx = click.get_current_context()

    if ctx.obj.get('config'):
        ctx.obj['config'].store.save()


@cli.command(short_help='Starts time tracking')
@click.pass_context
def start(ctx):
    if not ctx.obj['config'].store['running']:
        ctx.obj['provider'].start()


@cli.command(short_help='Stops time tracking')
@click.option('--description', '-d', help='Description for the running time entry')
@click.pass_context
def stop(ctx, description):
    if ctx.obj['config'].store['running']:
        ctx.obj['provider'].stop(description)


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
    ctx.obj['config'].store['since'] = datetime.now()


@cli.command('prompt', short_help='Handles integration to shell\'s prompt')
@click.option('--activate', cls=Mutex, not_required_if=('deactivate',), is_flag=True, help='Command will only activate the giTrack\'s prompt, no toggling.')
@click.option('--deactivate', cls=Mutex, not_required_if=('activate',), is_flag=True, help='Command will only deactivate the giTrack\'s prompt, no toggling.')
@click.option('--style', '-s', type=click.Choice(['simple', 'clock']),
              default='simple', help='Defines look of the installed prompt')
@click.pass_context
def prompt_cmd(ctx, activate, deactivate, style):
    """
    Command which activates/deactivates shell's prompt integration.

    \b
    This command needs to be ran as:
     - for Bash/ZSH: eval $(gitrack prompt)
     - for Fish: gitrack prompt | source -

    You can customize the command with additional options.
    """
    if activate:
        prompt.activate(style)
    elif deactivate:
        prompt.deactivate()
    else:
        prompt.execute(style)
