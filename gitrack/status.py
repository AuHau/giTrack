from datetime import datetime

import click

from . import helpers, config, exceptions


# TODO: [Bug/High] Optimize the execution time
def main():
    store = None
    try:
        repo_dir = helpers.get_repo_dir()
        store = config.Store(repo_dir)
    except (exceptions.UninitializedRepoException, RuntimeError):
        exit(2)  # No repo or not initialized repo ==> Nothing exciting for us

    if store.data.get('running') is not True:
        click.echo('0:0')
        exit(1)

    delta = datetime.now() - store.data['since']
    hours = divmod(delta.total_seconds(), 3600)
    minutes = divmod(hours[1], 60)
    seconds = minutes[1]

    if hours:
        click.echo('{:.0f}:{:.0f}'.format(minutes[0], seconds))
    else:
        click.echo('{:.0f}:{:.0f}:{:.0f}'.format(hours[0], minutes[0], seconds))


