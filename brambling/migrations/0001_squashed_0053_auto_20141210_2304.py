# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django_countries.fields
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    replaces = [(b'brambling', '0001_initial'), (b'brambling', '0002_auto_20140622_1737'), (b'brambling', '0003_auto_20140623_1209'), (b'brambling', '0004_auto_20140625_1729'), (b'brambling', '0005_auto_20140628_1720'), (b'brambling', '0006_auto_20140628_1724'), (b'brambling', '0007_auto_20140705_2009'), (b'brambling', '0008_auto_20140705_2010'), (b'brambling', '0009_auto_20140713_0556'), (b'brambling', '0010_eventperson_to_order'), (b'brambling', '0011_auto_20140713_0559'), (b'brambling', '0012_auto_20140713_0644'), (b'brambling', '0013_auto_20140715_2225'), (b'brambling', '0014_auto_20140715_2226'), (b'brambling', '0015_auto_20140715_2231'), (b'brambling', '0016_auto_20140717_1716'), (b'brambling', '0017_auto_20140717_1818'), (b'brambling', '0018_auto_20140717_1827'), (b'brambling', '0019_auto_20140718_0705'), (b'brambling', '0020_auto_20140807_2104'), (b'brambling', '0021_auto_20140807_2143'), (b'brambling', '0022_attendee_event_pass'), (b'brambling', '0023_auto_20140811_0505'), (b'brambling', '0024_auto_20140820_1914'), (b'brambling', '0025_auto_20140823_0402'), (b'brambling', '0026_auto_20140901_0618'), (b'brambling', '0027_auto_20140901_1955'), (b'brambling', '0028_itemimage'), (b'brambling', '0029_auto_20140910_1902'), (b'brambling', '0030_auto_20140910_1903'), (b'brambling', '0031_auto_20140910_2121'), (b'brambling', '0032_event_short_description'), (b'brambling', '0033_auto_20140914_0553'), (b'brambling', '0034_auto_20140914_0556'), (b'brambling', '0035_auto_20140914_2110'), (b'brambling', '0036_auto_20140915_1915'), (b'brambling', '0037_auto_20140916_2059'), (b'brambling', '0038_auto_20140919_2103'), (b'brambling', '0039_remove_event_tagline'), (b'brambling', '0040_auto_20141002_1804'), (b'brambling', '0041_auto_20141003_2241'), (b'brambling', '0042_auto_20141003_2242'), (b'brambling', '0043_remove_event_logo_image'), (b'brambling', '0044_auto_20141027_1936'), (b'brambling', '0045_auto_20141027_1952'), (b'brambling', '0046_event_application_fee_percent'), (b'brambling', '0047_order_email'), (b'brambling', '0048_auto_20141203_0219'), (b'brambling', '0049_auto_20141204_0205'), (b'brambling', '0050_auto_20141204_0209'), (b'brambling', '0051_event_check_zip'), (b'brambling', '0052_auto_20141205_2042'), (b'brambling', '0053_auto_20141210_2304')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '__first__'),
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
                ('groups', models.ManyToManyField(to=b'auth.Group', verbose_name='groups', blank=True)),
                ('user_permissions', models.ManyToManyField(to=b'auth.Permission', verbose_name='user permissions', blank=True)),
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
            field=models.ManyToManyField(to=b'brambling.DanceStyle', blank=True),
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
            field=models.ManyToManyField(to=b'brambling.Date', null=True, blank=True),
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
            field=models.ManyToManyField(to=b'brambling.DietaryRestriction', null=True, blank=True),
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
            field=models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b'People around me may be exposed to', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attendee',
            name='ef_avoid',
            field=models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b"I can't/don't want to be around", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='ef_cause',
            field=models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b'People around me may be exposed to', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='ef_avoid',
            field=models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b"I can't/don't want to be around", blank=True),
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
                ('dance_styles', models.ManyToManyField(to=b'brambling.DanceStyle', blank=True)),
                ('dates', models.ManyToManyField(to=b'brambling.Date')),
                ('editors', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('housing_dates', models.ManyToManyField(to=b'brambling.Date', null=True, blank=True)),
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
                ('ef_avoid', models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b"I/We don't want in my/our home", blank=True)),
                ('ef_present', models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b'People in the home may be exposed to', blank=True)),
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
                ('ef_avoid', models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b"I/We don't want in my/our home", blank=True)),
                ('ef_present', models.ManyToManyField(to=b'brambling.EnvironmentalFactor', null=True, verbose_name=b'People in my/our home may be exposed to', blank=True)),
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
            field=models.ManyToManyField(related_name=b'homes', null=True, verbose_name=b'My/Our home is (a/an)', to=b'brambling.HousingCategory', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='housing_categories',
            field=models.ManyToManyField(to=b'brambling.HousingCategory', null=True, verbose_name=b'Our home is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attendee',
            name='housing_prefer',
            field=models.ManyToManyField(related_name=b'event_preferred_by', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', to=b'brambling.HousingCategory', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='housing_prefer',
            field=models.ManyToManyField(to=b'brambling.HousingCategory', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', blank=True),
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
                ('price', models.DecimalField(max_digits=6, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('total_number', models.PositiveSmallIntegerField(help_text=b'Leave blank for unlimited.', null=True, blank=True)),
                ('available_start', models.DateTimeField(default=django.utils.timezone.now)),
                ('available_end', models.DateTimeField()),
                ('order', models.PositiveSmallIntegerField()),
                ('item', models.ForeignKey(related_name=b'options', to='brambling.Item')),
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
                ('remote_id', models.CharField(max_length=40, blank=True)),
                ('card', models.ForeignKey(to_field='id', blank=True, to='brambling.CreditCard', null=True)),
                ('order', models.ForeignKey(to='brambling.EventPerson', to_field='id')),
                ('method', models.CharField(default='stripe', max_length=6, choices=[(b'stripe', b'Stripe')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='person',
            name='modified_directly',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='ef_avoid_confirm',
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='ef_cause_confirm',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='ef_avoid_confirm',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='ef_present_confirm',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='housing_categories_confirm',
        ),
        migrations.CreateModel(
            name='BoughtItemDiscount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('bought_item', models.ForeignKey(to='brambling.BoughtItem', to_field='id')),
                ('discount', models.ForeignKey(to='brambling.Discount', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='boughtitemdiscount',
            unique_together=set([(b'bought_item', b'discount')]),
        ),
        migrations.CreateModel(
            name='EventPersonDiscount',
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
            name='eventpersondiscount',
            unique_together=set([(b'event_person', b'discount')]),
        ),
        migrations.AddField(
            model_name='discount',
            name='item_options',
            field=models.ManyToManyField(to=b'brambling.ItemOption'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='discount',
            name='item_option',
        ),
        migrations.AlterField(
            model_name='creditcard',
            name='person',
            field=models.ForeignKey(to_field='id', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='discount',
            name='available_end',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='discount',
            name='available_start',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='event',
            name='privacy',
            field=models.CharField(default=b'private', help_text=b'Who can view this event.', max_length=7, choices=[(b'public', 'List publicly'), (b'link', 'Visible to anyone with the link'), (b'private', 'Only visible to owner and editors')]),
        ),
        migrations.AlterField(
            model_name='item',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='person_avoid',
            field=models.TextField(verbose_name=b"I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='person_prefer',
            field=models.TextField(verbose_name=b'I/We would love to host', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='person_avoid',
            field=models.TextField(verbose_name=b"I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='person_prefer',
            field=models.TextField(verbose_name=b'I/We would love to host', blank=True),
        ),
        migrations.AlterField(
            model_name='discount',
            name='code',
            field=models.CharField(help_text=b'Allowed characters: 0-9, a-z, A-Z, space, and \'"~', max_length=20, validators=[django.core.validators.RegexValidator(b'[0-9A-Za-z \'"~]+')]),
        ),
        migrations.RenameModel(
            old_name='EventPerson',
            new_name='Order',
        ),
        migrations.RenameModel(
            old_name='EventPersonDiscount',
            new_name='OrderDiscount',
        ),
        migrations.RenameField(
            model_name='attendee',
            old_name='event_person',
            new_name='order',
        ),
        migrations.RenameField(
            model_name='boughtitem',
            old_name='event_person',
            new_name='order',
        ),
        migrations.RenameField(
            model_name='eventhousing',
            old_name='event_person',
            new_name='order',
        ),
        migrations.AddField(
            model_name='orderdiscount',
            name='order',
            field=models.ForeignKey(default=1, to='brambling.Order'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='orderdiscount',
            unique_together=set([(b'order', b'discount')]),
        ),
        migrations.RemoveField(
            model_name='orderdiscount',
            name='event_person',
        ),
        migrations.AddField(
            model_name='attendee',
            name='given_name',
            field=models.CharField(default='GIVENNAME', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attendee',
            name='middle_name',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attendee',
            name='name_order',
            field=models.CharField(default=b'GMS', max_length=3, choices=[(b'GMS', b'Given Middle Surname'), (b'SGM', b'Surname Given Middle'), (b'GS', b'Given Surname'), (b'SG', b'Surname Given')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attendee',
            name='surname',
            field=models.CharField(default='SURNAME', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='given_name',
            field=models.CharField(default='GIVENNAME', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='middle_name',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='name_order',
            field=models.CharField(default=b'GMS', max_length=3, choices=[(b'GMS', b'Given Middle Surname'), (b'SGM', b'Surname Given Middle'), (b'GS', b'Given Surname'), (b'SG', b'Surname Given')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='surname',
            field=models.CharField(default='SURNAME', max_length=50),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='name',
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='nickname',
        ),
        migrations.RemoveField(
            model_name='person',
            name='name',
        ),
        migrations.RemoveField(
            model_name='person',
            name='nickname',
        ),
        migrations.AddField(
            model_name='order',
            name='checked_out',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='order',
            name='cart_owners_set',
        ),
        migrations.AddField(
            model_name='order',
            name='code',
            field=models.CharField(default='', max_length=8, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order',
            name='person',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='order',
            unique_together=set([(b'event', b'code')]),
        ),
        migrations.AddField(
            model_name='event',
            name='liability_waiver',
            field=models.TextField(default='I hereby release {event}, its officers, and its employees from all liability of injury, loss, or damage to personal property associated with this event. I acknowledge that I understand the content of this document. I am aware that it is legally binding and I accept it out of my own free will.', help_text="'{event}' will be automatically replaced with your event name when users are presented with the waiver."),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='attendee',
            name='liability_waiver',
            field=models.BooleanField(default=False, help_text=b'Must be checked by the attendee themselves'),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='liability_waiver',
            field=models.BooleanField(default=False, help_text=b'Must be agreed to by the attendee themselves.'),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='person_avoid',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b'I do not want to be around these people', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='person_prefer',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b'I need to be placed with these people', blank=True),
        ),
        migrations.AddField(
            model_name='attendee',
            name='event_pass',
            field=models.OneToOneField(related_name=b'event_pass_for', to='brambling.BoughtItem'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('bought_item', models.ForeignKey(to='brambling.BoughtItem')),
                ('issuer', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(to='brambling.Order')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubPayment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('bought_item', models.ForeignKey(to='brambling.BoughtItem')),
                ('payment', models.ForeignKey(to='brambling.Payment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='subpayment',
            unique_together=set([(b'payment', b'bought_item')]),
        ),
        migrations.CreateModel(
            name='SubRefund',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('method', models.CharField(max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla'), (b'cash', b'Cash'), (b'check', b'Check'), (b'fake', b'Fake')])),
                ('remote_id', models.CharField(max_length=40, blank=True)),
                ('refund', models.ForeignKey(to='brambling.Refund')),
                ('subpayment', models.ForeignKey(related_name=b'refunds', to='brambling.SubPayment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='boughtitem',
            name='payments',
            field=models.ManyToManyField(to=b'brambling.Payment', through='brambling.SubPayment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_access_token',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_publishable_key',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_refresh_token',
            field=models.CharField(default=b'', max_length=60, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_user_id',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla')]),
        ),
        migrations.AddField(
            model_name='event',
            name='end_time',
            field=models.TimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='start_time',
            field=models.TimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='ItemImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField()),
                ('image', models.ImageField(upload_to=b'')),
                ('item', models.ForeignKey(related_name=b'images', to='brambling.Item')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla'), (b'cash', b'Cash'), (b'check', b'Check'), (b'fake', b'Fake')]),
        ),
        migrations.AddField(
            model_name='event',
            name='banner_image',
            field=models.ImageField(default='', upload_to=b'', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='website_url',
            field=models.URLField(default='', blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='attendee',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'attendee_avoid', null=True, verbose_name=b"I can't/don't want to be around", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='ef_cause',
            field=models.ManyToManyField(related_name=b'attendee_cause', null=True, verbose_name=b'People around me may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='order',
            field=models.ForeignKey(related_name=b'attendees', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='attendee',
            field=models.ForeignKey(related_name=b'bought_items', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.Attendee', null=True),
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='order',
            field=models.ForeignKey(related_name=b'bought_items', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='boughtitemdiscount',
            name='bought_item',
            field=models.ForeignKey(related_name=b'discounts', to='brambling.BoughtItem'),
        ),
        migrations.AlterField(
            model_name='creditcard',
            name='person',
            field=models.ForeignKey(related_name=b'cards', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='dates',
            field=models.ManyToManyField(related_name=b'event_dates', to=b'brambling.Date'),
        ),
        migrations.AlterField(
            model_name='event',
            name='editors',
            field=models.ManyToManyField(related_name=b'editor_events', null=True, to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='housing_dates',
            field=models.ManyToManyField(related_name=b'event_housing_dates', null=True, to=b'brambling.Date', blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(related_name=b'owner_events', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'eventhousing_avoid', null=True, verbose_name=b"I/We don't want in my/our home", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='ef_present',
            field=models.ManyToManyField(related_name=b'eventhousing_present', null=True, verbose_name=b'People in the home may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='housing_categories',
            field=models.ManyToManyField(related_name=b'eventhousing', null=True, verbose_name=b'Our home is (a/an)', to=b'brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'home_avoid', null=True, verbose_name=b"I/We don't want in my/our home", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='ef_present',
            field=models.ManyToManyField(related_name=b'home_present', null=True, verbose_name=b'People in my/our home may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='event',
            field=models.ForeignKey(related_name=b'items', to='brambling.Event'),
        ),
        migrations.AlterField(
            model_name='orderdiscount',
            name='order',
            field=models.ForeignKey(related_name=b'discounts', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(related_name=b'payments', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='person',
            name='default_card',
            field=models.OneToOneField(related_name=b'default_for', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.CreditCard'),
        ),
        migrations.AlterField(
            model_name='person',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'person_avoid', null=True, verbose_name=b"I can't/don't want to be around", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='ef_cause',
            field=models.ManyToManyField(related_name=b'person_cause', null=True, verbose_name=b'People around me may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='person',
            name='home',
            field=models.ForeignKey(related_name=b'residents', blank=True, to='brambling.Home', null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='housing_prefer',
            field=models.ManyToManyField(related_name=b'preferred_by', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', to=b'brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
        migrations.AlterField(
            model_name='refund',
            name='bought_item',
            field=models.ForeignKey(related_name=b'refunds', to='brambling.BoughtItem'),
        ),
        migrations.AlterField(
            model_name='refund',
            name='order',
            field=models.ForeignKey(related_name=b'refunds', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='subpayment',
            name='bought_item',
            field=models.ForeignKey(related_name=b'subpayments', to='brambling.BoughtItem'),
        ),
        migrations.AlterField(
            model_name='subpayment',
            name='payment',
            field=models.ForeignKey(related_name=b'subpayments', to='brambling.Payment'),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='phone',
            field=models.CharField(help_text=b'Required if requesting housing', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='contact_phone',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='contact_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name='event',
            name='description',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=20)),
                ('email', models.EmailField(max_length=75)),
                ('is_sent', models.BooleanField(default=False)),
                ('kind', models.CharField(max_length=6, choices=[(b'home', 'Home'), (b'editor', 'Editor')])),
                ('content_id', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='invite',
            unique_together=set([('email', 'content_id', 'kind')]),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='home',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.Home', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='is_frozen',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='is_published',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='privacy',
            field=models.CharField(default=b'public', help_text=b'Who can view this event.', max_length=7, choices=[(b'public', 'List publicly'), (b'link', 'Visible to anyone with the link')]),
        ),
        migrations.RemoveField(
            model_name='event',
            name='tagline',
        ),
        migrations.AlterField(
            model_name='event',
            name='country',
            field=django_countries.fields.CountryField(default=b'US', max_length=2, choices=[('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AS', 'American Samoa'), ('AD', 'Andorra'), ('AO', 'Angola'), ('AI', 'Anguilla'), ('AQ', 'Antarctica'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'), ('AW', 'Aruba'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'), ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BM', 'Bermuda'), ('BT', 'Bhutan'), ('BO', 'Bolivia, Plurinational State of'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BV', 'Bouvet Island'), ('BR', 'Brazil'), ('IO', 'British Indian Ocean Territory'), ('BN', 'Brunei Darussalam'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'), ('KY', 'Cayman Islands'), ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'), ('CX', 'Christmas Island'), ('CC', 'Cocos (Keeling) Islands'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo (the Democratic Republic of the)'), ('CK', 'Cook Islands'), ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CW', 'Cura\xe7ao'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'), ('CI', "C\xf4te d'Ivoire"), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'), ('FK', 'Falkland Islands  [Malvinas]'), ('FO', 'Faroe Islands'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GF', 'French Guiana'), ('PF', 'French Polynesia'), ('TF', 'French Southern Territories'), ('GA', 'Gabon'), ('GM', 'Gambia (The)'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GI', 'Gibraltar'), ('GR', 'Greece'), ('GL', 'Greenland'), ('GD', 'Grenada'), ('GP', 'Guadeloupe'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GG', 'Guernsey'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HM', 'Heard Island and McDonald Islands'), ('VA', 'Holy See  [Vatican City State]'), ('HN', 'Honduras'), ('HK', 'Hong Kong'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'), ('IR', 'Iran (the Islamic Republic of)'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JE', 'Jersey'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', "Korea (the Democratic People's Republic of)"), ('KR', 'Korea (the Republic of)'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', "Lao People's Democratic Republic"), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('MO', 'Macao'), ('MK', 'Macedonia (the former Yugoslav Republic of)'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MQ', 'Martinique'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('YT', 'Mayotte'), ('MX', 'Mexico'), ('FM', 'Micronesia (the Federated States of)'), ('MD', 'Moldova (the Republic of)'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MS', 'Montserrat'), ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NC', 'New Caledonia'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NU', 'Niue'), ('NF', 'Norfolk Island'), ('MP', 'Northern Mariana Islands'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'), ('PS', 'Palestine, State of'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PT', 'Portugal'), ('PR', 'Puerto Rico'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('RE', 'R\xe9union'), ('BL', 'Saint Barth\xe9lemy'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'), ('MF', 'Saint Martin (French part)'), ('PM', 'Saint Pierre and Miquelon'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SX', 'Sint Maarten (Dutch part)'), ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'), ('GS', 'South Georgia and the South Sandwich Islands'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'), ('SJ', 'Svalbard and Jan Mayen'), ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syrian Arab Republic'), ('TW', 'Taiwan (Province of China)'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania, United Republic of'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TK', 'Tokelau'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TC', 'Turks and Caicos Islands'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VN', 'Viet Nam'), ('VG', 'Virgin Islands (British)'), ('VI', 'Virgin Islands (U.S.)'), ('WF', 'Wallis and Futuna'), ('EH', 'Western Sahara'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'), ('AX', '\xc5land Islands')]),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='person_avoid',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b"I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='person_prefer',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b'I/We would love to host', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='person_avoid',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b"I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='person_prefer',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b'I/We would love to host', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='order',
            field=models.OneToOneField(related_name=b'eventhousing', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='phone',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='application_fee_percent',
            field=models.DecimalField(default=2.5, max_digits=5, decimal_places=2, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='email',
            field=models.EmailField(default='', max_length=75, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='check_address',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='check_city',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='check_country',
            field=django_countries.fields.CountryField(default=b'US', max_length=2, choices=[('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AS', 'American Samoa'), ('AD', 'Andorra'), ('AO', 'Angola'), ('AI', 'Anguilla'), ('AQ', 'Antarctica'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'), ('AW', 'Aruba'), ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'), ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'), ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BM', 'Bermuda'), ('BT', 'Bhutan'), ('BO', 'Bolivia, Plurinational State of'), ('BQ', 'Bonaire, Sint Eustatius and Saba'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BV', 'Bouvet Island'), ('BR', 'Brazil'), ('IO', 'British Indian Ocean Territory'), ('BN', 'Brunei Darussalam'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'), ('CV', 'Cape Verde'), ('KY', 'Cayman Islands'), ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'), ('CX', 'Christmas Island'), ('CC', 'Cocos (Keeling) Islands'), ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo (the Democratic Republic of the)'), ('CK', 'Cook Islands'), ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CW', 'Cura\xe7ao'), ('CY', 'Cyprus'), ('CZ', 'Czech Republic'), ('CI', "C\xf4te d'Ivoire"), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'), ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('ET', 'Ethiopia'), ('FK', 'Falkland Islands  [Malvinas]'), ('FO', 'Faroe Islands'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'), ('GF', 'French Guiana'), ('PF', 'French Polynesia'), ('TF', 'French Southern Territories'), ('GA', 'Gabon'), ('GM', 'Gambia (The)'), ('GE', 'Georgia'), ('DE', 'Germany'), ('GH', 'Ghana'), ('GI', 'Gibraltar'), ('GR', 'Greece'), ('GL', 'Greenland'), ('GD', 'Grenada'), ('GP', 'Guadeloupe'), ('GU', 'Guam'), ('GT', 'Guatemala'), ('GG', 'Guernsey'), ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'), ('HM', 'Heard Island and McDonald Islands'), ('VA', 'Holy See  [Vatican City State]'), ('HN', 'Honduras'), ('HK', 'Hong Kong'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'), ('ID', 'Indonesia'), ('IR', 'Iran (the Islamic Republic of)'), ('IQ', 'Iraq'), ('IE', 'Ireland'), ('IM', 'Isle of Man'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'), ('JE', 'Jersey'), ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'), ('KP', "Korea (the Democratic People's Republic of)"), ('KR', 'Korea (the Republic of)'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'), ('LA', "Lao People's Democratic Republic"), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'), ('LU', 'Luxembourg'), ('MO', 'Macao'), ('MK', 'Macedonia (the former Yugoslav Republic of)'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'), ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'), ('MQ', 'Martinique'), ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('YT', 'Mayotte'), ('MX', 'Mexico'), ('FM', 'Micronesia (the Federated States of)'), ('MD', 'Moldova (the Republic of)'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'), ('MS', 'Montserrat'), ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NC', 'New Caledonia'), ('NZ', 'New Zealand'), ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NU', 'Niue'), ('NF', 'Norfolk Island'), ('MP', 'Northern Mariana Islands'), ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'), ('PS', 'Palestine, State of'), ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'), ('PH', 'Philippines'), ('PN', 'Pitcairn'), ('PL', 'Poland'), ('PT', 'Portugal'), ('PR', 'Puerto Rico'), ('QA', 'Qatar'), ('RO', 'Romania'), ('RU', 'Russian Federation'), ('RW', 'Rwanda'), ('RE', 'R\xe9union'), ('BL', 'Saint Barth\xe9lemy'), ('SH', 'Saint Helena, Ascension and Tristan da Cunha'), ('KN', 'Saint Kitts and Nevis'), ('LC', 'Saint Lucia'), ('MF', 'Saint Martin (French part)'), ('PM', 'Saint Pierre and Miquelon'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'), ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'), ('SX', 'Sint Maarten (Dutch part)'), ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'), ('ZA', 'South Africa'), ('GS', 'South Georgia and the South Sandwich Islands'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'), ('SD', 'Sudan'), ('SR', 'Suriname'), ('SJ', 'Svalbard and Jan Mayen'), ('SZ', 'Swaziland'), ('SE', 'Sweden'), ('CH', 'Switzerland'), ('SY', 'Syrian Arab Republic'), ('TW', 'Taiwan (Province of China)'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania, United Republic of'), ('TH', 'Thailand'), ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TK', 'Tokelau'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'), ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TC', 'Turks and Caicos Islands'), ('TV', 'Tuvalu'), ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'), ('US', 'United States'), ('UM', 'United States Minor Outlying Islands'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'), ('VE', 'Venezuela, Bolivarian Republic of'), ('VN', 'Viet Nam'), ('VG', 'Virgin Islands (British)'), ('VI', 'Virgin Islands (U.S.)'), ('WF', 'Wallis and Futuna'), ('EH', 'Western Sahara'), ('YE', 'Yemen'), ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'), ('AX', '\xc5land Islands')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='check_postmark_cutoff',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='check_payable_to',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='check_payment_allowed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='check_recipient',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='check_state_or_province',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payment',
            name='is_confirmed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='check_zip',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='check_address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='zip_code',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='zip_code',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='send_flyers_address_2',
            field=models.CharField(default='', max_length=200, verbose_name=b'address line 2', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='send_flyers_zip',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
    ]
