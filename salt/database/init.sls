postgres:
  pkg.installed:
    - name: postgresql
  service.running:
    - name: postgresql
    - require:
      - pkg: postgresql

webproject_db_user:
  postgres_user.present:
    - name: {{ pillar['connections']['db']['user']}}
    - password: {{ pillar['connections']['db']['password']}}

webproject_db:
  postgres_database.present:
    - name: {{ pillar['connections']['db']['name']}}
    - owner: {{ pillar['connections']['db']['user']}}
    - require:
      - postgres_user: webproject_db_user
