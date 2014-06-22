# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django_countries.fields
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0002_auto_20140622_1221'),
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('confirmed_email', models.EmailField(max_length=254)),
                ('name', models.CharField(help_text='First Last. Must contain only letters and spaces, with a minimum of 1 space.', max_length=100, verbose_name=b'Full name', validators=[django.core.validators.RegexValidator(b'^\\w+( \\w+)+')])),
                ('nickname', models.CharField(max_length=50, blank=True)),
                ('phone', models.CharField(max_length=50, blank=True)),
                ('created_timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('is_active', models.BooleanField(default=True)),
                ('person_prefer', models.TextField(verbose_name=b'I need to be placed with', blank=True)),
                ('person_avoid', models.TextField(verbose_name=b'I do not want to be around', blank=True)),
                ('other_needs', models.TextField(blank=True)),
                ('stripe_customer_id', models.CharField(max_length=36, blank=True)),
                ('groups', models.ManyToManyField(to='auth.Group', verbose_name='groups', blank=True)),
                ('user_permissions', models.ManyToManyField(to='auth.Permission', verbose_name='user permissions', blank=True)),
            ],
            options={
                'verbose_name': 'person',
                'verbose_name_plural': 'people',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Attendee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person_confirmed', models.BooleanField(default=False)),
                ('basic_completed', models.BooleanField(default=False)),
                ('name', models.CharField(help_text='First Last. Must contain only letters and spaces, with a minimum of 1 space.', max_length=100, verbose_name=b'Full name', validators=[django.core.validators.RegexValidator(b'^\\w+( \\w+)+')])),
                ('nickname', models.CharField(max_length=50, blank=True)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=50, blank=True)),
                ('liability_waiver', models.BooleanField(default=False)),
                ('photo_consent', models.BooleanField(default=False, verbose_name=b'I consent to have my photo taken at this event.')),
                ('housing_status', models.CharField(default=b'have', max_length=4, verbose_name=b'housing status', choices=[(b'need', b'Needs housing'), (b'have', b'Already arranged'), (b'home', b'Staying at own home')])),
                ('housing_completed', models.BooleanField(default=False)),
                ('ef_cause_confirm', models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'})),
                ('ef_avoid_confirm', models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'})),
                ('person_prefer', models.TextField(verbose_name=b'I need to be placed with', blank=True)),
                ('person_avoid', models.TextField(verbose_name=b'I do not want to be around', blank=True)),
                ('other_needs', models.TextField(blank=True)),
                ('person', models.ForeignKey(to_field='id', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BoughtItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default=b'unpaid', max_length=8, choices=[(b'reserved', 'Reserved'), (b'unpaid', 'Unpaid'), (b'paid', 'Paid'), (b'refunded', 'Refunded')])),
                ('attendee', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to_field='id', blank=True, to='brambling.Attendee', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CreditCard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_card_id', models.CharField(max_length=40)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('exp_month', models.PositiveSmallIntegerField()),
                ('exp_year', models.PositiveSmallIntegerField()),
                ('fingerprint', models.CharField(max_length=32)),
                ('last4', models.CharField(max_length=4)),
                ('brand', models.CharField(max_length=16)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='person',
            name='default_card',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to_field='id', blank=True, to='brambling.CreditCard'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='creditcard',
            name='person',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='DanceStyle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='person',
            name='dance_styles',
            field=models.ManyToManyField(to='brambling.DanceStyle', blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Date',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
            ],
            options={
                'ordering': (b'date',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='attendee',
            name='nights',
            field=models.ManyToManyField(to='brambling.Date', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='DietaryRestriction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='person',
            name='dietary_restrictions',
            field=models.ManyToManyField(to='brambling.DietaryRestriction', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('code', models.CharField(max_length=20)),
                ('available_start', models.DateTimeField(null=True, blank=True)),
                ('available_end', models.DateTimeField(null=True, blank=True)),
                ('discount_type', models.CharField(default=b'flat', max_length=7, choices=[(b'flat', 'Flat'), (b'percent', 'Percent')])),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EnvironmentalFactor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='attendee',
            name='ef_cause',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b'People around me will be exposed to', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attendee',
            name='ef_avoid',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b"I can't/don't want to be around", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='ef_cause',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b'People around me will be exposed to', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='ef_avoid',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b"I can't/don't want to be around", blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(help_text=b'URL-friendly version of the event name. Dashes, 0-9, and lower-case a-z only.', unique=True, validators=[django.core.validators.RegexValidator(b'[a-z0-9-]+')])),
                ('tagline', models.CharField(max_length=75, blank=True)),
                ('city', models.CharField(max_length=50)),
                ('state_or_province', models.CharField(max_length=50)),
                ('country', django_countries.fields.CountryField(max_length=2, choices=[('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AS', 'American Samoa'), ('AD', 'Andorra'), ('AO', 'Angola'), ('AI', 'Anguilla'), ('AQ', 'Antarctica'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'), ('AW', 'Aruba'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'), ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BM', 'Bermuda'), ('BT', 'Bhutan'), ('BO', 'Bolivia, Plurinational State of'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BV', 'Bouvet Island'), ('BR', 'Brazil'), ('IO', 'British Indian Ocean Territory'), ('BN', 'Brunei Darussalam'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'), ('KY', 'Cayman Islands'), ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'), ('CX', 'Christmas Island'), ('CC', 'Cocos (Keeling) Islands'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo (the Democratic Republic of the)'), ('CK', 'Cook Islands'), ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CW', 'Cura\xe7ao'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'), ('CI', "C\xf4te d'Ivoire"), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'), ('FK', 'Falkland Islands  [Malvinas]'), ('FO', 'Faroe Islands'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GF', 'French Guiana'), ('PF', 'French Polynesia'), ('TF', 'French Southern Territories'), ('GA', 'Gabon'), ('GM', 'Gambia (The)'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GI', 'Gibraltar'), ('GR', 'Greece'), ('GL', 'Greenland'), ('GD', 'Grenada'), ('GP', 'Guadeloupe'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GG', 'Guernsey'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HM', 'Heard Island and McDonald Islands'), ('VA', 'Holy See  [Vatican City State]'), ('HN', 'Honduras'), ('HK', 'Hong Kong'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'), ('IR', 'Iran (the Islamic Republic of)'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JE', 'Jersey'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', "Korea (the Democratic People's Republic of)"), ('KR', 'Korea (the Republic of)'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', "Lao People's Democratic Republic"), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('MO', 'Macao'), ('MK', 'Macedonia (the former Yugoslav Republic of)'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MQ', 'Martinique'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('YT', 'Mayotte'), ('MX', 'Mexico'), ('FM', 'Micronesia (the Federated States of)'), ('MD', 'Moldova (the Republic of)'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MS', 'Montserrat'), ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NC', 'New Caledonia'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NU', 'Niue'), ('NF', 'Norfolk Island'), ('MP', 'Northern Mariana Islands'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'), ('PS', 'Palestine, State of'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PT', 'Portugal'), ('PR', 'Puerto Rico'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('RE', 'R\xe9union'), ('BL', 'Saint Barth\xe9lemy'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'), ('MF', 'Saint Martin (French part)'), ('PM', 'Saint Pierre and Miquelon'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SX', 'Sint Maarten (Dutch part)'), ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'), ('GS', 'South Georgia and the South Sandwich Islands'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'), ('SJ', 'Svalbard and Jan Mayen'), ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syrian Arab Republic'), ('TW', 'Taiwan (Province of China)'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania, United Republic of'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TK', 'Tokelau'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TC', 'Turks and Caicos Islands'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VN', 'Viet Nam'), ('VG', 'Virgin Islands (British)'), ('VI', 'Virgin Islands (U.S.)'), ('WF', 'Wallis and Futuna'), ('EH', 'Western Sahara'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'), ('AX', '\xc5land Islands')])),
                ('timezone', models.CharField(default=b'UTC', max_length=40)),
                ('currency', models.CharField(default=b'USD', max_length=10)),
                ('has_dances', models.BooleanField(default=False, verbose_name=b'Is a dance / Has dance(s)')),
                ('has_classes', models.BooleanField(default=False, verbose_name=b'Is a class / Has class(es)')),
                ('privacy', models.CharField(default=b'public', help_text=b'Who can view this event.', max_length=7, choices=[(b'public', 'List publicly'), (b'link', 'Visible to anyone with the link'), (b'private', 'Only visible to owner and editors')])),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('collect_housing_data', models.BooleanField(default=True)),
                ('collect_survey_data', models.BooleanField(default=True)),
                ('cart_timeout', models.PositiveSmallIntegerField(default=15, help_text=b"Minutes before a user's cart expires.")),
                ('dance_styles', models.ManyToManyField(to='brambling.DanceStyle', blank=True)),
                ('dates', models.ManyToManyField(to='brambling.Date')),
                ('editors', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('housing_dates', models.ManyToManyField(to='brambling.Date', null=True, blank=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='discount',
            name='event',
            field=models.ForeignKey(to='brambling.Event', to_field='id'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='EventHousing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contact_name', models.CharField(help_text='First Last. Must contain only letters and spaces, with a minimum of 1 space.', max_length=100, validators=[django.core.validators.RegexValidator(b'^\\w+( \\w+)+')])),
                ('contact_email', models.EmailField(max_length=75, blank=True)),
                ('contact_phone', models.CharField(max_length=50, blank=True)),
                ('address', models.CharField(max_length=200)),
                ('city', models.CharField(max_length=50)),
                ('state_or_province', models.CharField(max_length=50)),
                ('country', django_countries.fields.CountryField(max_length=2, choices=[('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AS', 'American Samoa'), ('AD', 'Andorra'), ('AO', 'Angola'), ('AI', 'Anguilla'), ('AQ', 'Antarctica'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'), ('AW', 'Aruba'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'), ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BM', 'Bermuda'), ('BT', 'Bhutan'), ('BO', 'Bolivia, Plurinational State of'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BV', 'Bouvet Island'), ('BR', 'Brazil'), ('IO', 'British Indian Ocean Territory'), ('BN', 'Brunei Darussalam'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'), ('KY', 'Cayman Islands'), ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'), ('CX', 'Christmas Island'), ('CC', 'Cocos (Keeling) Islands'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo (the Democratic Republic of the)'), ('CK', 'Cook Islands'), ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CW', 'Cura\xe7ao'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'), ('CI', "C\xf4te d'Ivoire"), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'), ('FK', 'Falkland Islands  [Malvinas]'), ('FO', 'Faroe Islands'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GF', 'French Guiana'), ('PF', 'French Polynesia'), ('TF', 'French Southern Territories'), ('GA', 'Gabon'), ('GM', 'Gambia (The)'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GI', 'Gibraltar'), ('GR', 'Greece'), ('GL', 'Greenland'), ('GD', 'Grenada'), ('GP', 'Guadeloupe'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GG', 'Guernsey'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HM', 'Heard Island and McDonald Islands'), ('VA', 'Holy See  [Vatican City State]'), ('HN', 'Honduras'), ('HK', 'Hong Kong'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'), ('IR', 'Iran (the Islamic Republic of)'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JE', 'Jersey'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', "Korea (the Democratic People's Republic of)"), ('KR', 'Korea (the Republic of)'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', "Lao People's Democratic Republic"), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('MO', 'Macao'), ('MK', 'Macedonia (the former Yugoslav Republic of)'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MQ', 'Martinique'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('YT', 'Mayotte'), ('MX', 'Mexico'), ('FM', 'Micronesia (the Federated States of)'), ('MD', 'Moldova (the Republic of)'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MS', 'Montserrat'), ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NC', 'New Caledonia'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NU', 'Niue'), ('NF', 'Norfolk Island'), ('MP', 'Northern Mariana Islands'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'), ('PS', 'Palestine, State of'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PT', 'Portugal'), ('PR', 'Puerto Rico'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('RE', 'R\xe9union'), ('BL', 'Saint Barth\xe9lemy'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'), ('MF', 'Saint Martin (French part)'), ('PM', 'Saint Pierre and Miquelon'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SX', 'Sint Maarten (Dutch part)'), ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'), ('GS', 'South Georgia and the South Sandwich Islands'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'), ('SJ', 'Svalbard and Jan Mayen'), ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syrian Arab Republic'), ('TW', 'Taiwan (Province of China)'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania, United Republic of'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TK', 'Tokelau'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TC', 'Turks and Caicos Islands'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VN', 'Viet Nam'), ('VG', 'Virgin Islands (British)'), ('VI', 'Virgin Islands (U.S.)'), ('WF', 'Wallis and Futuna'), ('EH', 'Western Sahara'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'), ('AX', '\xc5land Islands')])),
                ('public_transit_access', models.BooleanField(default=False, verbose_name=b'My/Our house has easy access to public transit')),
                ('ef_present_confirm', models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'})),
                ('ef_avoid_confirm', models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'})),
                ('person_prefer', models.TextField(help_text=b'Include resident preferences', verbose_name=b'I/We would love to host', blank=True)),
                ('person_avoid', models.TextField(help_text=b'Include resident preferences', verbose_name=b"I/We don't want to host", blank=True)),
                ('housing_categories_confirm', models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'})),
                ('ef_avoid', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b"I/We don't want in my/our home", blank=True)),
                ('ef_present', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b'People in the home will be exposed to', blank=True)),
                ('event', models.ForeignKey(to='brambling.Event', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPerson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cart_start_time', models.DateTimeField(null=True, blank=True)),
                ('cart_owners_set', models.BooleanField(default=False)),
                ('survey_completed', models.BooleanField(default=False)),
                ('heard_through', models.CharField(blank=True, max_length=8, choices=[(b'flyer', b'Flyer'), (b'facebook', b'Facebook'), (b'website', b'Event website'), (b'internet', b'Other website'), (b'friend', b'Friend'), (b'attendee', b'Former attendee'), (b'dancer', b'Other dancer'), (b'other', b'Other')])),
                ('heard_through_other', models.CharField(max_length=128, blank=True)),
                ('send_flyers', models.BooleanField(default=False)),
                ('send_flyers_address', models.CharField(max_length=200, verbose_name=b'address', blank=True)),
                ('send_flyers_city', models.CharField(max_length=50, verbose_name=b'city', blank=True)),
                ('send_flyers_state_or_province', models.CharField(max_length=50, verbose_name=b'state or province', blank=True)),
                ('send_flyers_country', django_countries.fields.CountryField(blank=True, max_length=2, verbose_name=b'country', choices=[('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AS', 'American Samoa'), ('AD', 'Andorra'), ('AO', 'Angola'), ('AI', 'Anguilla'), ('AQ', 'Antarctica'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'), ('AW', 'Aruba'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'), ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BM', 'Bermuda'), ('BT', 'Bhutan'), ('BO', 'Bolivia, Plurinational State of'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BV', 'Bouvet Island'), ('BR', 'Brazil'), ('IO', 'British Indian Ocean Territory'), ('BN', 'Brunei Darussalam'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'), ('KY', 'Cayman Islands'), ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'), ('CX', 'Christmas Island'), ('CC', 'Cocos (Keeling) Islands'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo (the Democratic Republic of the)'), ('CK', 'Cook Islands'), ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CW', 'Cura\xe7ao'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'), ('CI', "C\xf4te d'Ivoire"), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'), ('FK', 'Falkland Islands  [Malvinas]'), ('FO', 'Faroe Islands'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GF', 'French Guiana'), ('PF', 'French Polynesia'), ('TF', 'French Southern Territories'), ('GA', 'Gabon'), ('GM', 'Gambia (The)'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GI', 'Gibraltar'), ('GR', 'Greece'), ('GL', 'Greenland'), ('GD', 'Grenada'), ('GP', 'Guadeloupe'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GG', 'Guernsey'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HM', 'Heard Island and McDonald Islands'), ('VA', 'Holy See  [Vatican City State]'), ('HN', 'Honduras'), ('HK', 'Hong Kong'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'), ('IR', 'Iran (the Islamic Republic of)'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JE', 'Jersey'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', "Korea (the Democratic People's Republic of)"), ('KR', 'Korea (the Republic of)'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', "Lao People's Democratic Republic"), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('MO', 'Macao'), ('MK', 'Macedonia (the former Yugoslav Republic of)'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MQ', 'Martinique'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('YT', 'Mayotte'), ('MX', 'Mexico'), ('FM', 'Micronesia (the Federated States of)'), ('MD', 'Moldova (the Republic of)'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MS', 'Montserrat'), ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NC', 'New Caledonia'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NU', 'Niue'), ('NF', 'Norfolk Island'), ('MP', 'Northern Mariana Islands'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'), ('PS', 'Palestine, State of'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PT', 'Portugal'), ('PR', 'Puerto Rico'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('RE', 'R\xe9union'), ('BL', 'Saint Barth\xe9lemy'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'), ('MF', 'Saint Martin (French part)'), ('PM', 'Saint Pierre and Miquelon'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SX', 'Sint Maarten (Dutch part)'), ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'), ('GS', 'South Georgia and the South Sandwich Islands'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'), ('SJ', 'Svalbard and Jan Mayen'), ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syrian Arab Republic'), ('TW', 'Taiwan (Province of China)'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania, United Republic of'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TK', 'Tokelau'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TC', 'Turks and Caicos Islands'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VN', 'Viet Nam'), ('VG', 'Virgin Islands (British)'), ('VI', 'Virgin Islands (U.S.)'), ('WF', 'Wallis and Futuna'), ('EH', 'Western Sahara'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'), ('AX', '\xc5land Islands')])),
                ('providing_housing', models.BooleanField(default=False)),
                ('event', models.ForeignKey(to='brambling.Event', to_field='id')),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='event_person',
            field=models.ForeignKey(to='brambling.EventPerson', to_field='id'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boughtitem',
            name='event_person',
            field=models.ForeignKey(to='brambling.EventPerson', to_field='id'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attendee',
            name='event_person',
            field=models.ForeignKey(to='brambling.EventPerson', to_field='id'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Home',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.CharField(max_length=200)),
                ('city', models.CharField(max_length=50)),
                ('state_or_province', models.CharField(max_length=50)),
                ('country', django_countries.fields.CountryField(max_length=2, choices=[('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AS', 'American Samoa'), ('AD', 'Andorra'), ('AO', 'Angola'), ('AI', 'Anguilla'), ('AQ', 'Antarctica'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'), ('AW', 'Aruba'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'), ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BM', 'Bermuda'), ('BT', 'Bhutan'), ('BO', 'Bolivia, Plurinational State of'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BV', 'Bouvet Island'), ('BR', 'Brazil'), ('IO', 'British Indian Ocean Territory'), ('BN', 'Brunei Darussalam'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'), ('KY', 'Cayman Islands'), ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'), ('CX', 'Christmas Island'), ('CC', 'Cocos (Keeling) Islands'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo (the Democratic Republic of the)'), ('CK', 'Cook Islands'), ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CW', 'Cura\xe7ao'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'), ('CI', "C\xf4te d'Ivoire"), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'), ('FK', 'Falkland Islands  [Malvinas]'), ('FO', 'Faroe Islands'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GF', 'French Guiana'), ('PF', 'French Polynesia'), ('TF', 'French Southern Territories'), ('GA', 'Gabon'), ('GM', 'Gambia (The)'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GI', 'Gibraltar'), ('GR', 'Greece'), ('GL', 'Greenland'), ('GD', 'Grenada'), ('GP', 'Guadeloupe'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GG', 'Guernsey'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HM', 'Heard Island and McDonald Islands'), ('VA', 'Holy See  [Vatican City State]'), ('HN', 'Honduras'), ('HK', 'Hong Kong'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'), ('IR', 'Iran (the Islamic Republic of)'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JE', 'Jersey'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', "Korea (the Democratic People's Republic of)"), ('KR', 'Korea (the Republic of)'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', "Lao People's Democratic Republic"), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('MO', 'Macao'), ('MK', 'Macedonia (the former Yugoslav Republic of)'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MQ', 'Martinique'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('YT', 'Mayotte'), ('MX', 'Mexico'), ('FM', 'Micronesia (the Federated States of)'), ('MD', 'Moldova (the Republic of)'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MS', 'Montserrat'), ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NC', 'New Caledonia'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NU', 'Niue'), ('NF', 'Norfolk Island'), ('MP', 'Northern Mariana Islands'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'), ('PS', 'Palestine, State of'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PT', 'Portugal'), ('PR', 'Puerto Rico'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('RE', 'R\xe9union'), ('BL', 'Saint Barth\xe9lemy'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'), ('MF', 'Saint Martin (French part)'), ('PM', 'Saint Pierre and Miquelon'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SX', 'Sint Maarten (Dutch part)'), ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'), ('GS', 'South Georgia and the South Sandwich Islands'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'), ('SJ', 'Svalbard and Jan Mayen'), ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syrian Arab Republic'), ('TW', 'Taiwan (Province of China)'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania, United Republic of'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TK', 'Tokelau'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TC', 'Turks and Caicos Islands'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VN', 'Viet Nam'), ('VG', 'Virgin Islands (British)'), ('VI', 'Virgin Islands (U.S.)'), ('WF', 'Wallis and Futuna'), ('EH', 'Western Sahara'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'), ('AX', '\xc5land Islands')])),
                ('public_transit_access', models.BooleanField(default=False, verbose_name=b'My/Our house has easy access to public transit')),
                ('person_prefer', models.TextField(help_text=b'Include resident preferences', verbose_name=b'I/We would love to host', blank=True)),
                ('person_avoid', models.TextField(help_text=b'Include resident preferences', verbose_name=b"I/We don't want to host", blank=True)),
                ('ef_avoid', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b"I/We don't want in my/our home", blank=True)),
                ('ef_present', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b'People in my/our home will be exposed to', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='home',
            field=models.ForeignKey(to_field='id', blank=True, to='brambling.Home', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='home',
            field=models.ForeignKey(to_field='id', blank=True, to='brambling.Home', null=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='HousingAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assignment_type', models.CharField(max_length=6, choices=[(b'auto', 'Automatic'), (b'manual', 'Manual')])),
                ('attendee', models.ForeignKey(to='brambling.Attendee', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HousingCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='home',
            name='housing_categories',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name=b'My/Our home is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='housing_categories',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name=b'Our home is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attendee',
            name='housing_prefer',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='housing_prefer',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='HousingSlot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('spaces', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
                ('spaces_max', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
                ('eventhousing', models.ForeignKey(to='brambling.EventHousing', to_field='id')),
                ('night', models.ForeignKey(to='brambling.Date', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='housingassignment',
            name='slot',
            field=models.ForeignKey(to='brambling.HousingSlot', to_field='id'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField()),
                ('category', models.CharField(max_length=7, choices=[(b'merch', 'Merchandise'), (b'comp', 'Competition'), (b'class', 'Class/Lesson a la carte'), (b'pass', 'Pass')])),
                ('created_timestamp', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(to='brambling.Event', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('price', models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('total_number', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('available_start', models.DateTimeField(default=django.utils.timezone.now)),
                ('available_end', models.DateTimeField()),
                ('order', models.PositiveSmallIntegerField()),
                ('item', models.ForeignKey(to='brambling.Item', to_field='id')),
            ],
            options={
                'ordering': (b'order',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='discount',
            name='item_option',
            field=models.ForeignKey(to='brambling.ItemOption', to_field='id'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='discount',
            unique_together=set([(b'code', b'event')]),
        ),
        migrations.AddField(
            model_name='boughtitem',
            name='item_option',
            field=models.ForeignKey(to='brambling.ItemOption', to_field='id'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('stripe_charge_id', models.CharField(max_length=40, blank=True)),
                ('card', models.ForeignKey(to_field='id', blank=True, to='brambling.CreditCard', null=True)),
                ('event_person', models.ForeignKey(to='brambling.EventPerson', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UsedDiscount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('discount', models.ForeignKey(to='brambling.Discount', to_field='id')),
                ('event_person', models.ForeignKey(to='brambling.EventPerson', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='useddiscount',
            unique_together=set([(b'event_person', b'discount')]),
        ),
    ]
