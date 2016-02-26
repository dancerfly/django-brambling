from fabric.api import task, run, sudo, cd, env
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project


env.use_ssh_config = True
REPO_SLUG = 'django-brambling'
REPO_URL = "https://github.com/littleweaver/" + REPO_SLUG + ".git"
DEFAULT_BRANCH = 'master'


@task
def install_salt():
    run("curl -L https://bootstrap.saltstack.com | sudo sh -s -- -P git v2016.3")


@task
def sync_pillar():
    if not exists('/srv/pillar'):
        sudo('mkdir /srv/pillar')
    rsync_project(local_dir='pillar/', remote_dir='/srv/pillar/')


@task
def deploy_code(branch_or_commit=DEFAULT_BRANCH):
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
    sudo("salt-call --local state.highstate")


@task
def deploy(branch_or_commit=DEFAULT_BRANCH):
    sync_pillar()
    deploy_code(branch_or_commit)
    salt_call()


@task
def manage(command):
    full_command = "/bin/bash -l -c 'source /var/www/env/bin/activate && python /var/www/project/manage.py {0}'".format(command)
    sudo(full_command, user="webproject")


@task
def restart_gunicorn():
    sudo('circusctl restart gunicorn')
