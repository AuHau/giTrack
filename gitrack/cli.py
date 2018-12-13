import click

from . import helpers, config


# TODO: Handling --ammend
# TODO: Parsing commit message/branch name for Task ID
# TODO: Offline mode?

def entrypoint(args, obj=None):
    """
    CLI entry point, where exceptions are handled.
    """
    cli(args, obj=obj or {})


@click.group()
@click.pass_context
def cli(ctx):
    repo = helpers.get_repo()
    ctx.obj['repo'] = repo

    if ctx.invoked_subcommand != 'init':
        ctx.obj['config'] = config.Config(repo)
        ctx.obj['provider'] = ctx.obj['config'].provider_class(ctx.obj['config'])


@cli.command(short_help='Starts time tracking')
@click.pass_context
def start(ctx):
    ctx.obj['provider'].start()


@cli.command(short_help='Stops time tracking')
@click.option('--description', '-d', help='Description for the running time entry')
@click.pass_context
def stop(ctx, description):
    ctx.obj['provider'].stop(description)


@cli.command(short_help='Initialize Git repo for time tracking')
@click.option('--config-destination', '-c', type=click.Choice(['local', 'store']),
              default='local',
              help='Specifies where to store the configuration for the initialized repository. '
                   '\'local\' means file in the root of the Git repository. '
                   '\'store\' means giTrack\'s internal storage. Default: local')
@click.pass_context
def init(ctx, config_destination):
    repo = ctx.obj['repo']
    helpers.init(repo, config.ConfigDestination(config_destination))


@cli.group(short_help='Git hooks invocations')
@click.pass_context
def hooks(ctx):
    pass


@hooks.command('post-commit', short_help='Post-commit git hook')
@click.pass_context
def hooks_post_commit(ctx):
    provider = ctx.obj['provider']
    repo = ctx.obj['repo']
    commit = repo.head.commit
    message = commit.message.strip()

    provider.stop(message)
    provider.start()
