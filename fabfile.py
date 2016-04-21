import os
from functools import wraps

from fabric.api import task, run, sudo, cd, env
from fabric.contrib.files import exists
from fabric.operations import local, put, require
from fabric.utils import abort


env.use_ssh_config = True
REPO_SLUG = 'django-brambling'
REPO_URL = "https://github.com/littleweaver/" + REPO_SLUG + ".git"
PILLAR_REPO_URL = "git@github.com:littleweaver/dancerfly-pillar.git"
DEFAULT_BRANCH = 'master'
CURRENT_DIR = os.path.dirname(__file__)


TIERS = {
    'production': {
        'hosts': ['root@104.131.92.59'],
    },
    'staging': {
        'hosts': ['root@162.243.226.226'],
    },
}

def forbid_in_tiers(*forbidden_tiers):

    def func_wrapper(func):
        @wraps(func)
        def returned_wrapper(*args, **kwargs):
            if env.get('tier') in forbidden_tiers:
                msg = ('This command cannot run on the {} tier.'.format(env.tier))
                msg += "\n\nTry one of these tiers instead: {}".format(
                    ', '.join(set(TIERS.keys()) - set(forbidden_tiers))
                )
                abort(msg)
            else:
                return func(*args, **kwargs)
        return returned_wrapper
    return func_wrapper


def tier_set(tier_name='staging'):
    env.tier = tier_name
    for option, value in TIERS[env.tier].items():
        setattr(env, option, value)


@task
def production():
    tier_set('production')


@task
def staging():
    tier_set('staging')


@task
def install_salt():
    require('tier', provided_by=(staging, production))
    run("curl -L https://bootstrap.saltstack.com | sudo sh -s -- -P git a6c0907")


@task
def sync_pillar(branch_or_commit='master'):
    require('tier', provided_by=(staging, production))
    if not os.path.exists(os.path.join(CURRENT_DIR, 'pillar')):
        local("git clone {} pillar".format(PILLAR_REPO_URL))
    if not exists('/root/.ssh/id_rsa'):
        put(local_path='pillar/id_rsa',
            remote_path='/root/.ssh/id_rsa',
            mode='0400')
    if not exists('/srv/pillar'):
        sudo("git clone {} /srv/pillar".format(PILLAR_REPO_URL))
    with cd('/srv/pillar'):
        sudo('git fetch')
        sudo('git stash')
        sudo('git checkout {}'.format(branch_or_commit))
        sudo('git reset --hard origin/{}'.format(branch_or_commit))


@task
def deploy_code(branch_or_commit=DEFAULT_BRANCH):
    require('tier', provided_by=(staging, production))
    if not exists('/var/www/'):
        sudo('mkdir /var/www')
    with cd("/var/www"):
        project_dir = "/var/www/{}".format(REPO_SLUG)
        if not exists(project_dir):
            sudo("git clone {}".format(REPO_URL))
        with cd(REPO_SLUG):
            sudo('git fetch')
            sudo('git stash')
            sudo('git checkout {}'.format(branch_or_commit))
            sudo('git reset --hard origin/{}'.format(branch_or_commit))
            sudo('chmod -R a+rw {}'.format(project_dir))
            sudo('rm -rf /srv/salt')
            sudo('mkdir /srv/salt')
            sudo("cp -R salt/* /srv/salt")


@task
def salt_call():
    require('tier', provided_by=(staging, production))
    sudo("salt-call --local state.highstate")


@task
def deploy(branch_or_commit=DEFAULT_BRANCH):
    require('tier', provided_by=(staging, production))
    if not run('which salt-call', quiet=True):
        install_salt()
    sync_pillar()
    deploy_code(branch_or_commit)
    salt_call()
    manage('migrate --noinput')
    manage('collectstatic --noinput')


@task
def manage(command):
    require('tier', provided_by=(staging, production))
    full_command = "/bin/bash -l -c 'source /var/www/env/bin/activate && python /var/www/project/manage.py {0}'".format(command)
    sudo(full_command, user="webproject")


@task
def restart_gunicorn():
    require('tier', provided_by=(staging, production))
    sudo('circusctl restart gunicorn')
