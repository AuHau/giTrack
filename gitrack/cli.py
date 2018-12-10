import click

from toggl import api

from . import git, config


# TODO: Handling --ammend


def entrypoint(args, obj=None):
    """
    CLI entry point, where exceptions are handled.
    """
    cli(args, obj=obj or {})


@click.group()
@click.pass_context
def cli(ctx):
    pass


@cli.command(short_help='Starts time tracking')
def start():
    api.TimeEntry.start_and_save()


@cli.command(short_help='Stops time tracking')
@click.option('--description', '-d', help='Description for the running time entry')
def stop(description):
    entry = api.TimeEntry.objects.current()  # type: api.TimeEntry
    entry.description = description
    entry.stop_and_save()


@cli.command(short_help='Initialize Git repo for time tracking')
def init():
    repo = git.get_repo()
    git.intall_hook(repo)
    config.Store.init_repo(repo)


@cli.group(short_help='Git hooks invocations')
@click.pass_context
def hooks(ctx):
    pass


@hooks.command('post-commit', short_help='Post-commit git hook')
@click.pass_context
def hooks_post_commit(ctx):
    repo = git.get_repo()
    commit = repo.head.commit

    entry = api.TimeEntry.objects.current()  # type: api.TimeEntry
    entry.description = commit.message.strip()
    entry.stop_and_save()

    api.TimeEntry.start_and_save()
