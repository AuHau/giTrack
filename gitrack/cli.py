import logging
import os
import traceback
from datetime import datetime

import click
import click_completion
import git
import inquirer

from gitrack import helpers, prompt, config as config_module, __version__, exceptions

click_completion.init()

logger = logging.getLogger('gitrack.cli')


# Ideas for future
# TODO: [?] Offline mode
# TODO: Automatic pausing using file activities (watchdog)


#################################################################
# Custom classes for Click


class Mutex(click.Option):
    """
    Class that implements exclusive options for Click

    Credits to: https://stackoverflow.com/questions/44247099/click-command-line-interfaces-make-options-required-if-other-optional-option-is
    """

    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")

        if not self.not_required_if:
            raise AssertionError("'not_required_if' parameter required")

        kwargs["help"] = (kwargs.get("help", "") + "Option is mutually exclusive with "
                          + ", ".join(self.not_required_if) + ".").strip()
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts:
                if current_opt:
                    raise click.UsageError("Illegal usage: '" + str(self.name) +
                                           "' is mutually exclusive with " + str(mutex_opt) + ".")
                else:
                    self.prompt = None
        return super().handle_parse_result(ctx, opts, args)


def entrypoint(args, obj=None):
    """
    CLI entry point, where exceptions are handled.
    """
    try:
        cli(args, obj=obj or {})
    except exceptions.GitrackException as e:
        logger.error(str(e).strip())
        logger.debug(traceback.format_exc())
        exit(1)
    except Exception as e:
        if os.environ.get('GITRACK_EXCEPTIONS') == '1':
            raise

        logger.error(str(e).strip())
        logger.debug(traceback.format_exc())
        exit(1)


@click.group()
@click.option('--quiet', '-q', is_flag=True, help="Don't print anything")
@click.option('--verbose', '-v', count=True, help="Prints additional info. More Vs, more info! (-vvv...)")
@click.version_option(__version__)
@click.pass_context
def cli(ctx, quiet, verbose):
    """
    Tool for automating time tracking using Git. It heavily depends on Git hooks.
    Time entries are created based on the commits, their messages and time of creation.

    Configuration is handled on three levels: store > local config > global config.
    Store is an internal giTrack's data storage, where data are written during initialization.
    Local config is an .gitrack file placed in root of the Git repository and hence bound to the repository.
    Global config is a file placed in system's location for application configs.
    For Linux: ~/.config/gitrack/default.config.
    For MacOS: ~/Library/Application Support/gitrack/default.config. It is config where the common setting for all
    repositories.

    Before using giTrack you have to initialize the Git's repository: 'gitrack init'.
    Afterwards when you start tracking your work use: 'gitrack start', after your are finished run 'gitrack stop'.
    """
    repo_dir = helpers.get_repo_dir()
    ctx.obj['repo_dir'] = repo_dir

    main_logger = logging.getLogger('gitrack')
    main_logger.setLevel(logging.DEBUG)

    # Logging to Stderr
    default = logging.StreamHandler()
    default_formatter = logging.Formatter('%(levelname)s: %(message)s')
    default.setFormatter(default_formatter)

    if verbose == 1:
        default.setLevel(logging.INFO)
    elif verbose == 2:
        default.setLevel(logging.DEBUG)
    else:
        default.setLevel(logging.ERROR)

    if quiet:
        # TODO: [Q/Design] Is this good idea?
        click.echo = lambda *args, **kwargs: None
    else:
        main_logger.addHandler(default)

    if ctx.invoked_subcommand != 'init':
        ctx.obj['config'] = config_module.Config(repo_dir)

        provider_class = ctx.obj['config'].provider.klass()
        ctx.obj['provider'] = provider_class(ctx.obj['config'])


@cli.resultcallback()
def save_store(*args, **kwargs):
    ctx = click.get_current_context()

    if ctx.obj.get('config'):
        config = ctx.obj.get('config')
        config.store.save()

        # We don't want to pollute certain invocations
        if ctx.invoked_subcommand not in {'prompt', 'hooks'} \
            and config.update_check:
            
            helpers.check_version()


@cli.command(short_help='Starts time tracking')
@click.option('--force', is_flag=True, help='Will force creation of the time entry.')
@click.pass_context
def start(ctx, force):
    """
    Starts the time tracking.
    """
    logger.debug("What does Store things about this repo? Is it currently running?: {}"
                 .format(ctx.obj['config'].store['running']))
    if not ctx.obj['config'].store['running']:
        try:
            ctx.obj['provider'].start(force)
        except exceptions.RunningEntry:
            overwrite = inquirer.shortcuts.confirm('There is currently running time entry that '
                                                   'will be overwritten, do you want to continue?', default=False)

            if overwrite:
                ctx.obj['provider'].start(force=True)


@cli.command(short_help='Stops time tracking')
@click.option('--cancel', '-c', is_flag=True,
              help='If the currently running time entry should be canceled and not saved.')
@click.option('--description', '-d', help='Description for the running time entry')
@click.pass_context
def stop(ctx, cancel, description):
    """
    Stops the time tracking with message if provided.
    """
    if ctx.obj['config'].store['running']:
        if cancel:
            ctx.obj['provider'].cancel()
        else:
            ctx.obj['provider'].stop(description)


@cli.command(short_help='Initialize Git repo for time tracking')
@click.option('--check', is_flag=True, help='Instead of initializing the repo, checks whether it has '
                                            'been initialized before. If not exits the command with exit code 2')
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
    """
    Initializes the current Git repository.

    \b
    There are two places where the bootstrapped information can be stored:
      - internal storage (store)
      - local config (local) - file in root of the repository

    It is possible to initialize giTrack without automatic installation of the Git's hook.
    Then it is your responsibility to ensure that on 'post-commit' hook the giTrack command
    'gitrack hooks post-commit' is called.
    """
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
def hooks():
    """
    Internal group of commands for handling Git's hooks
    """
    pass


@hooks.command('post-commit', short_help='Post-commit git hook')
@click.option('--force', is_flag=True, help='Will force creation of the time entry.')
@click.pass_context
def hooks_post_commit(ctx, force):
    """
    Internal command which is being called on Git's post-commit hook.
    It is responsible for creating the new time entries.
    """

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

    provider.stop(message, task=task, project=project, force=force)
    provider.start()
    ctx.obj['config'].store['since'] = datetime.now()


@cli.command('prompt', short_help='Handles integration to shell\'s prompt')
@click.option('--activate', cls=Mutex, not_required_if=('deactivate',), is_flag=True,
              help='Command will only activate the giTrack\'s prompt, no toggling.')
@click.option('--deactivate', cls=Mutex, not_required_if=('activate',), is_flag=True,
              help='Command will only deactivate the giTrack\'s prompt, no toggling.')
@click.option('--style', '-s', type=click.Choice(['simple', 'clock']),
              default='simple', help='Defines look of the installed prompt')
def prompt_cmd(activate, deactivate, style):
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


cmd_help = """Shell completion for gitrack command

Available shell types:

\b
  {}

Default type: auto
""".format("\n  ".join('{:<12} {}'.format(k, click_completion.core.shells[k]) for k in sorted(
    click_completion.core.shells.keys())))


@cli.group(help=cmd_help, short_help='Shell completion for gitrack command')
def completion():
    pass


@completion.command()
@click.option('-i', '--case-insensitive/--no-case-insensitive', help="Case insensitive completion")
@click.argument('shell', required=False, type=click_completion.DocumentedChoice(click_completion.core.shells))
def show(shell, case_insensitive):
    """Show the toggl completion code"""
    extra_env = {'_GITRACK_CASE_INSENSITIVE_COMPLETE': 'ON'} if case_insensitive else {}
    click.echo(click_completion.core.get_code(shell, extra_env=extra_env))


@completion.command()
@click.option('--append/--overwrite', help="Append the completion code to the file", default=None)
@click.option('-i', '--case-insensitive/--no-case-insensitive', help="Case insensitive completion")
@click.argument('shell', required=False, type=click_completion.DocumentedChoice(click_completion.core.shells))
@click.argument('path', required=False)
def install(append, case_insensitive, shell, path):
    """Install the toggl completion"""
    extra_env = {'_GITRACK_CASE_INSENSITIVE_COMPLETE': 'ON'} if case_insensitive else {}
    shell, path = click_completion.core.install(shell=shell, path=path, append=append, extra_env=extra_env)
    click.echo('%s completion installed in %s' % (shell, path))
