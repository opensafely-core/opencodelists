from fabric.api import abort, env, prefix, run, task
from fabric.context_managers import cd, shell_env
from fabric.contrib.files import exists

env.forward_agent = True
env.colorize_errors = True

env.hosts = ["smallweb1.ebmdatalab.net"]
env.user = "root"
env.path = "/var/www/opencodelists"
env.use_ssh_config = True


def initalise_directory():
    if not exists(env.path):
        run(f"git clone git@github.com:ebmdatalab/opencodelists.git {env.path}")


def check_environment():
    environment_path = "{}/environment".format(env.path)

    if not exists(environment_path):
        abort("Create {} before proceeding".format(environment_path))


def create_venv():
    if not exists("venv"):
        run("python3.6 -m venv venv")


def update_from_git():
    run("git fetch --all")
    run("git checkout --force origin/master")


def install_python_requirements():
    with prefix("source venv/bin/activate"):
        run("pip install --quiet --requirement requirements.txt")


def chown_everything():
    run(f"chown -R www-data:www-data {env.path}")


def run_migrations():
    with prefix("source venv/bin/activate"):
        run("python manage.py migrate")


def install_js_requirements():
    run("npm install --no-progress")


def build_static_assets():
    run("npm run build")


def set_up_nginx():
    run(
        f"ln -sf {env.path}/deploy/nginx/opencodelists /etc/nginx/sites-enabled/opencodelists"
    )

    run("/etc/init.d/nginx reload")


def set_up_systemd():
    run(
        f"ln -sf {env.path}/deploy/systemd/app.opencodelists.web.service /etc/systemd/system"
    )

    run("systemctl daemon-reload")


def restart_service():
    run("systemctl restart app.opencodelists.web.service")


def notify_sentry():
    # get current sha
    sha = run("git rev-parse --short HEAD")

    # get Sentry deploy URL from the environment file
    release_url = run(
        "grep SENTRY_DEPLOY_URL environment | awk -F\"'\" '{ print $2}'", shell=True
    )

    # post the new version name to Sentry
    # this command was taken from the releases page:
    # https://sentry.io/settings/ebm-datalab/projects/opencodelists/release-tracking/
    payload = f'{{"version": "{sha}"}}'
    run(
        f"curl {release_url} -X POST -H 'Content-Type: application/json' -d '{payload}'"
    )


@task
def deploy():
    initalise_directory()
    check_environment()

    with cd(env.path):
        with shell_env(DJANGO_SETTINGS_MODULE="opencodelists.settings"):
            create_venv()
            update_from_git()
            install_python_requirements()
            run_migrations()
            install_js_requirements()
            build_static_assets()
            chown_everything()
            set_up_nginx()
            set_up_systemd()
            restart_service()
            notify_sentry()
