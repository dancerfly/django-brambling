newrelic-repo:
  pkgrepo.managed:
    - name: deb http://apt.newrelic.com/debian/ newrelic non-free
    - key_url: https://download.newrelic.com/548C16BF.gpg

newrelic-sysmond:
  pkg.installed:
    - require:
      - pkgrepo: newrelic-repo
  service.running:
    - watch:
      - pkg: newrelic-sysmond
      - file: newrelic-sysmond-conf
    - require:
      - file: newrelic-sysmond-conf

newrelic-sysmond-conf:
  file.managed:
    - name: /etc/newrelic/nrsysmond.cfg
    - source: salt://monitoring/nrsysmond.cfg.jinja
    - template: jinja
    - require:
      - pkg: newrelic-sysmond
