# encoding: utf8
from django.db import models, migrations
import django_countries.fields
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.CharField(max_length=50)),
                ('tagline', models.CharField(max_length=75)),
                ('city', models.CharField(max_length=50)),
                ('state_or_province', models.CharField(max_length=50)),
                ('country', django_countries.fields.CountryField(max_length=2, choices=[(u'AF', u'Afghanistan'), (u'AL', u'Albania'), (u'DZ', u'Algeria'), (u'AS', u'American Samoa'), (u'AD', u'Andorra'), (u'AO', u'Angola'), (u'AI', u'Anguilla'), (u'AQ', u'Antarctica'), (u'AG', u'Antigua and Barbuda'), (u'AR', u'Argentina'), (u'AM', u'Armenia'), (u'AW', u'Aruba'), (u'AU', u'Australia'), (u'AT', u'Austria'), (u'AZ', u'Azerbaijan'), (u'BS', u'Bahamas'), (u'BH', u'Bahrain'), (u'BD', u'Bangladesh'), (u'BB', u'Barbados'), (u'BY', u'Belarus'), (u'BE', u'Belgium'), (u'BZ', u'Belize'), (u'BJ', u'Benin'), (u'BM', u'Bermuda'), (u'BT', u'Bhutan'), (u'BO', u'Bolivia, Plurinational State of'), (u'BQ', u'Bonaire, Sint Eustatius and Saba'), (u'BA', u'Bosnia and Herzegovina'), (u'BW', u'Botswana'), (u'BV', u'Bouvet Island'), (u'BR', u'Brazil'), (u'IO', u'British Indian Ocean Territory'), (u'BN', u'Brunei Darussalam'), (u'BG', u'Bulgaria'), (u'BF', u'Burkina Faso'), (u'BI', u'Burundi'), (u'KH', u'Cambodia'), (u'CM', u'Cameroon'), (u'CA', u'Canada'), (u'CV', u'Cape Verde'), (u'KY', u'Cayman Islands'), (u'CF', u'Central African Republic'), (u'TD', u'Chad'), (u'CL', u'Chile'), (u'CN', u'China'), (u'CX', u'Christmas Island'), (u'CC', u'Cocos (Keeling) Islands'), (u'CO', u'Colombia'), (u'KM', u'Comoros'), (u'CG', u'Congo'), (u'CD', u'Congo (the Democratic Republic of the)'), (u'CK', u'Cook Islands'), (u'CR', u'Costa Rica'), (u'HR', u'Croatia'), (u'CU', u'Cuba'), (u'CW', u'Cura\xe7ao'), (u'CY', u'Cyprus'), (u'CZ', u'Czech Republic'), (u'CI', u"C\xf4te d'Ivoire"), (u'DK', u'Denmark'), (u'DJ', u'Djibouti'), (u'DM', u'Dominica'), (u'DO', u'Dominican Republic'), (u'EC', u'Ecuador'), (u'EG', u'Egypt'), (u'SV', u'El Salvador'), (u'GQ', u'Equatorial Guinea'), (u'ER', u'Eritrea'), (u'EE', u'Estonia'), (u'ET', u'Ethiopia'), (u'FK', u'Falkland Islands  [Malvinas]'), (u'FO', u'Faroe Islands'), (u'FJ', u'Fiji'), (u'FI', u'Finland'), (u'FR', u'France'), (u'GF', u'French Guiana'), (u'PF', u'French Polynesia'), (u'TF', u'French Southern Territories'), (u'GA', u'Gabon'), (u'GM', u'Gambia (The)'), (u'GE', u'Georgia'), (u'DE', u'Germany'), (u'GH', u'Ghana'), (u'GI', u'Gibraltar'), (u'GR', u'Greece'), (u'GL', u'Greenland'), (u'GD', u'Grenada'), (u'GP', u'Guadeloupe'), (u'GU', u'Guam'), (u'GT', u'Guatemala'), (u'GG', u'Guernsey'), (u'GN', u'Guinea'), (u'GW', u'Guinea-Bissau'), (u'GY', u'Guyana'), (u'HT', u'Haiti'), (u'HM', u'Heard Island and McDonald Islands'), (u'VA', u'Holy See  [Vatican City State]'), (u'HN', u'Honduras'), (u'HK', u'Hong Kong'), (u'HU', u'Hungary'), (u'IS', u'Iceland'), (u'IN', u'India'), (u'ID', u'Indonesia'), (u'IR', u'Iran (the Islamic Republic of)'), (u'IQ', u'Iraq'), (u'IE', u'Ireland'), (u'IM', u'Isle of Man'), (u'IL', u'Israel'), (u'IT', u'Italy'), (u'JM', u'Jamaica'), (u'JP', u'Japan'), (u'JE', u'Jersey'), (u'JO', u'Jordan'), (u'KZ', u'Kazakhstan'), (u'KE', u'Kenya'), (u'KI', u'Kiribati'), (u'KP', u"Korea (the Democratic People's Republic of)"), (u'KR', u'Korea (the Republic of)'), (u'KW', u'Kuwait'), (u'KG', u'Kyrgyzstan'), (u'LA', u"Lao People's Democratic Republic"), (u'LV', u'Latvia'), (u'LB', u'Lebanon'), (u'LS', u'Lesotho'), (u'LR', u'Liberia'), (u'LY', u'Libya'), (u'LI', u'Liechtenstein'), (u'LT', u'Lithuania'), (u'LU', u'Luxembourg'), (u'MO', u'Macao'), (u'MK', u'Macedonia (the former Yugoslav Republic of)'), (u'MG', u'Madagascar'), (u'MW', u'Malawi'), (u'MY', u'Malaysia'), (u'MV', u'Maldives'), (u'ML', u'Mali'), (u'MT', u'Malta'), (u'MH', u'Marshall Islands'), (u'MQ', u'Martinique'), (u'MR', u'Mauritania'), (u'MU', u'Mauritius'), (u'YT', u'Mayotte'), (u'MX', u'Mexico'), (u'FM', u'Micronesia (the Federated States of)'), (u'MD', u'Moldova (the Republic of)'), (u'MC', u'Monaco'), (u'MN', u'Mongolia'), (u'ME', u'Montenegro'), (u'MS', u'Montserrat'), (u'MA', u'Morocco'), (u'MZ', u'Mozambique'), (u'MM', u'Myanmar'), (u'NA', u'Namibia'), (u'NR', u'Nauru'), (u'NP', u'Nepal'), (u'NL', u'Netherlands'), (u'NC', u'New Caledonia'), (u'NZ', u'New Zealand'), (u'NI', u'Nicaragua'), (u'NE', u'Niger'), (u'NG', u'Nigeria'), (u'NU', u'Niue'), (u'NF', u'Norfolk Island'), (u'MP', u'Northern Mariana Islands'), (u'NO', u'Norway'), (u'OM', u'Oman'), (u'PK', u'Pakistan'), (u'PW', u'Palau'), (u'PS', u'Palestine, State of'), (u'PA', u'Panama'), (u'PG', u'Papua New Guinea'), (u'PY', u'Paraguay'), (u'PE', u'Peru'), (u'PH', u'Philippines'), (u'PN', u'Pitcairn'), (u'PL', u'Poland'), (u'PT', u'Portugal'), (u'PR', u'Puerto Rico'), (u'QA', u'Qatar'), (u'RO', u'Romania'), (u'RU', u'Russian Federation'), (u'RW', u'Rwanda'), (u'RE', u'R\xe9union'), (u'BL', u'Saint Barth\xe9lemy'), (u'SH', u'Saint Helena, Ascension and Tristan da Cunha'), (u'KN', u'Saint Kitts and Nevis'), (u'LC', u'Saint Lucia'), (u'MF', u'Saint Martin (French part)'), (u'PM', u'Saint Pierre and Miquelon'), (u'VC', u'Saint Vincent and the Grenadines'), (u'WS', u'Samoa'), (u'SM', u'San Marino'), (u'ST', u'Sao Tome and Principe'), (u'SA', u'Saudi Arabia'), (u'SN', u'Senegal'), (u'RS', u'Serbia'), (u'SC', u'Seychelles'), (u'SL', u'Sierra Leone'), (u'SG', u'Singapore'), (u'SX', u'Sint Maarten (Dutch part)'), (u'SK', u'Slovakia'), (u'SI', u'Slovenia'), (u'SB', u'Solomon Islands'), (u'SO', u'Somalia'), (u'ZA', u'South Africa'), (u'GS', u'South Georgia and the South Sandwich Islands'), (u'SS', u'South Sudan'), (u'ES', u'Spain'), (u'LK', u'Sri Lanka'), (u'SD', u'Sudan'), (u'SR', u'Suriname'), (u'SJ', u'Svalbard and Jan Mayen'), (u'SZ', u'Swaziland'), (u'SE', u'Sweden'), (u'CH', u'Switzerland'), (u'SY', u'Syrian Arab Republic'), (u'TW', u'Taiwan (Province of China)'), (u'TJ', u'Tajikistan'), (u'TZ', u'Tanzania, United Republic of'), (u'TH', u'Thailand'), (u'TL', u'Timor-Leste'), (u'TG', u'Togo'), (u'TK', u'Tokelau'), (u'TO', u'Tonga'), (u'TT', u'Trinidad and Tobago'), (u'TN', u'Tunisia'), (u'TR', u'Turkey'), (u'TM', u'Turkmenistan'), (u'TC', u'Turks and Caicos Islands'), (u'TV', u'Tuvalu'), (u'UG', u'Uganda'), (u'UA', u'Ukraine'), (u'AE', u'United Arab Emirates'), (u'GB', u'United Kingdom'), (u'US', u'United States'), (u'UM', u'United States Minor Outlying Islands'), (u'UY', u'Uruguay'), (u'UZ', u'Uzbekistan'), (u'VU', u'Vanuatu'), (u'VE', u'Venezuela, Bolivarian Republic of'), (u'VN', u'Viet Nam'), (u'VG', u'Virgin Islands (British)'), (u'VI', u'Virgin Islands (U.S.)'), (u'WF', u'Wallis and Futuna'), (u'EH', u'Western Sahara'), (u'YE', u'Yemen'), (u'ZM', u'Zambia'), (u'ZW', u'Zimbabwe'), (u'AX', u'\xc5land Islands')])),
                ('currency', models.CharField(default='USD', max_length=10)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('category', models.CharField(max_length=8, choices=[('workshop', u'Workshop weekend'), ('exchange', u'Exchange'), ('recess', u'Recess'), ('other', u'Other')])),
                ('handle_housing', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventUserInfo',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(to='brambling.Event', to_field=u'id')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('roles', models.CharField(max_length=6, choices=[('lead', u'Lead'), ('follow', u'Follow'), ('switch', u'Switch'), ('ambi', u'Ambi')])),
                ('house_spaces', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
                ('nights', models.CommaSeparatedIntegerField(max_length=50)),
                ('car_spaces', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(50)])),
                ('bedtime', models.CharField(max_length=5, choices=[('late', u'Staying up late'), ('early', u'Going to bed early')])),
                ('wakeup', models.CharField(max_length=5, choices=[('late', u'Staying up late'), ('early', u'Going to bed early')])),
                ('avoid_problems', models.CommaSeparatedIntegerField(max_length=16, blank=True)),
                ('avoid_problems_other', models.CharField(max_length=50, blank=True)),
                ('cause_problems', models.CommaSeparatedIntegerField(max_length=16, blank=True)),
                ('cause_problems_other', models.CharField(max_length=50, blank=True)),
                ('other', models.TextField(blank=True)),
                ('request_matches', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('request_unmatches', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField()),
                ('category', models.CharField(max_length=7, choices=[('merch', u'Merchandise'), ('comp', u'Competition'), ('private', u'Private lesson'), ('pass', u'Pass')])),
                ('event', models.ForeignKey(to='brambling.Event', to_field=u'id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DiscountCode',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=20)),
                ('available_start', models.DateTimeField()),
                ('available_end', models.DateTimeField()),
                ('items', models.ManyToManyField(to='brambling.Item')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemDiscount',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('item', models.ForeignKey(to='brambling.Item', to_field=u'id')),
                ('discount', models.ForeignKey(to='brambling.DiscountCode', to_field=u'id')),
                ('percent', models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)])),
                ('amount', models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemOption',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('item', models.ForeignKey(to='brambling.Item', to_field=u'id')),
                ('name', models.CharField(max_length=30, blank=True)),
                ('price', models.DecimalField(max_digits=5, decimal_places=2)),
                ('total_number', models.PositiveSmallIntegerField()),
                ('available_start', models.DateTimeField()),
                ('available_end', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(to='brambling.Event', to_field=u'id')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserDiscount',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('discount', models.ForeignKey(to='brambling.DiscountCode', to_field=u'id')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserItem',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('item_option', models.ForeignKey(to='brambling.ItemOption', to_field=u'id')),
                ('reserved', models.DateTimeField(default=django.utils.timezone.now)),
                ('paid', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('city', models.CharField(max_length=50)),
                ('state_or_province', models.CharField(max_length=50)),
                ('country', django_countries.fields.CountryField(max_length=2, choices=[(u'AF', u'Afghanistan'), (u'AL', u'Albania'), (u'DZ', u'Algeria'), (u'AS', u'American Samoa'), (u'AD', u'Andorra'), (u'AO', u'Angola'), (u'AI', u'Anguilla'), (u'AQ', u'Antarctica'), (u'AG', u'Antigua and Barbuda'), (u'AR', u'Argentina'), (u'AM', u'Armenia'), (u'AW', u'Aruba'), (u'AU', u'Australia'), (u'AT', u'Austria'), (u'AZ', u'Azerbaijan'), (u'BS', u'Bahamas'), (u'BH', u'Bahrain'), (u'BD', u'Bangladesh'), (u'BB', u'Barbados'), (u'BY', u'Belarus'), (u'BE', u'Belgium'), (u'BZ', u'Belize'), (u'BJ', u'Benin'), (u'BM', u'Bermuda'), (u'BT', u'Bhutan'), (u'BO', u'Bolivia, Plurinational State of'), (u'BQ', u'Bonaire, Sint Eustatius and Saba'), (u'BA', u'Bosnia and Herzegovina'), (u'BW', u'Botswana'), (u'BV', u'Bouvet Island'), (u'BR', u'Brazil'), (u'IO', u'British Indian Ocean Territory'), (u'BN', u'Brunei Darussalam'), (u'BG', u'Bulgaria'), (u'BF', u'Burkina Faso'), (u'BI', u'Burundi'), (u'KH', u'Cambodia'), (u'CM', u'Cameroon'), (u'CA', u'Canada'), (u'CV', u'Cape Verde'), (u'KY', u'Cayman Islands'), (u'CF', u'Central African Republic'), (u'TD', u'Chad'), (u'CL', u'Chile'), (u'CN', u'China'), (u'CX', u'Christmas Island'), (u'CC', u'Cocos (Keeling) Islands'), (u'CO', u'Colombia'), (u'KM', u'Comoros'), (u'CG', u'Congo'), (u'CD', u'Congo (the Democratic Republic of the)'), (u'CK', u'Cook Islands'), (u'CR', u'Costa Rica'), (u'HR', u'Croatia'), (u'CU', u'Cuba'), (u'CW', u'Cura\xe7ao'), (u'CY', u'Cyprus'), (u'CZ', u'Czech Republic'), (u'CI', u"C\xf4te d'Ivoire"), (u'DK', u'Denmark'), (u'DJ', u'Djibouti'), (u'DM', u'Dominica'), (u'DO', u'Dominican Republic'), (u'EC', u'Ecuador'), (u'EG', u'Egypt'), (u'SV', u'El Salvador'), (u'GQ', u'Equatorial Guinea'), (u'ER', u'Eritrea'), (u'EE', u'Estonia'), (u'ET', u'Ethiopia'), (u'FK', u'Falkland Islands  [Malvinas]'), (u'FO', u'Faroe Islands'), (u'FJ', u'Fiji'), (u'FI', u'Finland'), (u'FR', u'France'), (u'GF', u'French Guiana'), (u'PF', u'French Polynesia'), (u'TF', u'French Southern Territories'), (u'GA', u'Gabon'), (u'GM', u'Gambia (The)'), (u'GE', u'Georgia'), (u'DE', u'Germany'), (u'GH', u'Ghana'), (u'GI', u'Gibraltar'), (u'GR', u'Greece'), (u'GL', u'Greenland'), (u'GD', u'Grenada'), (u'GP', u'Guadeloupe'), (u'GU', u'Guam'), (u'GT', u'Guatemala'), (u'GG', u'Guernsey'), (u'GN', u'Guinea'), (u'GW', u'Guinea-Bissau'), (u'GY', u'Guyana'), (u'HT', u'Haiti'), (u'HM', u'Heard Island and McDonald Islands'), (u'VA', u'Holy See  [Vatican City State]'), (u'HN', u'Honduras'), (u'HK', u'Hong Kong'), (u'HU', u'Hungary'), (u'IS', u'Iceland'), (u'IN', u'India'), (u'ID', u'Indonesia'), (u'IR', u'Iran (the Islamic Republic of)'), (u'IQ', u'Iraq'), (u'IE', u'Ireland'), (u'IM', u'Isle of Man'), (u'IL', u'Israel'), (u'IT', u'Italy'), (u'JM', u'Jamaica'), (u'JP', u'Japan'), (u'JE', u'Jersey'), (u'JO', u'Jordan'), (u'KZ', u'Kazakhstan'), (u'KE', u'Kenya'), (u'KI', u'Kiribati'), (u'KP', u"Korea (the Democratic People's Republic of)"), (u'KR', u'Korea (the Republic of)'), (u'KW', u'Kuwait'), (u'KG', u'Kyrgyzstan'), (u'LA', u"Lao People's Democratic Republic"), (u'LV', u'Latvia'), (u'LB', u'Lebanon'), (u'LS', u'Lesotho'), (u'LR', u'Liberia'), (u'LY', u'Libya'), (u'LI', u'Liechtenstein'), (u'LT', u'Lithuania'), (u'LU', u'Luxembourg'), (u'MO', u'Macao'), (u'MK', u'Macedonia (the former Yugoslav Republic of)'), (u'MG', u'Madagascar'), (u'MW', u'Malawi'), (u'MY', u'Malaysia'), (u'MV', u'Maldives'), (u'ML', u'Mali'), (u'MT', u'Malta'), (u'MH', u'Marshall Islands'), (u'MQ', u'Martinique'), (u'MR', u'Mauritania'), (u'MU', u'Mauritius'), (u'YT', u'Mayotte'), (u'MX', u'Mexico'), (u'FM', u'Micronesia (the Federated States of)'), (u'MD', u'Moldova (the Republic of)'), (u'MC', u'Monaco'), (u'MN', u'Mongolia'), (u'ME', u'Montenegro'), (u'MS', u'Montserrat'), (u'MA', u'Morocco'), (u'MZ', u'Mozambique'), (u'MM', u'Myanmar'), (u'NA', u'Namibia'), (u'NR', u'Nauru'), (u'NP', u'Nepal'), (u'NL', u'Netherlands'), (u'NC', u'New Caledonia'), (u'NZ', u'New Zealand'), (u'NI', u'Nicaragua'), (u'NE', u'Niger'), (u'NG', u'Nigeria'), (u'NU', u'Niue'), (u'NF', u'Norfolk Island'), (u'MP', u'Northern Mariana Islands'), (u'NO', u'Norway'), (u'OM', u'Oman'), (u'PK', u'Pakistan'), (u'PW', u'Palau'), (u'PS', u'Palestine, State of'), (u'PA', u'Panama'), (u'PG', u'Papua New Guinea'), (u'PY', u'Paraguay'), (u'PE', u'Peru'), (u'PH', u'Philippines'), (u'PN', u'Pitcairn'), (u'PL', u'Poland'), (u'PT', u'Portugal'), (u'PR', u'Puerto Rico'), (u'QA', u'Qatar'), (u'RO', u'Romania'), (u'RU', u'Russian Federation'), (u'RW', u'Rwanda'), (u'RE', u'R\xe9union'), (u'BL', u'Saint Barth\xe9lemy'), (u'SH', u'Saint Helena, Ascension and Tristan da Cunha'), (u'KN', u'Saint Kitts and Nevis'), (u'LC', u'Saint Lucia'), (u'MF', u'Saint Martin (French part)'), (u'PM', u'Saint Pierre and Miquelon'), (u'VC', u'Saint Vincent and the Grenadines'), (u'WS', u'Samoa'), (u'SM', u'San Marino'), (u'ST', u'Sao Tome and Principe'), (u'SA', u'Saudi Arabia'), (u'SN', u'Senegal'), (u'RS', u'Serbia'), (u'SC', u'Seychelles'), (u'SL', u'Sierra Leone'), (u'SG', u'Singapore'), (u'SX', u'Sint Maarten (Dutch part)'), (u'SK', u'Slovakia'), (u'SI', u'Slovenia'), (u'SB', u'Solomon Islands'), (u'SO', u'Somalia'), (u'ZA', u'South Africa'), (u'GS', u'South Georgia and the South Sandwich Islands'), (u'SS', u'South Sudan'), (u'ES', u'Spain'), (u'LK', u'Sri Lanka'), (u'SD', u'Sudan'), (u'SR', u'Suriname'), (u'SJ', u'Svalbard and Jan Mayen'), (u'SZ', u'Swaziland'), (u'SE', u'Sweden'), (u'CH', u'Switzerland'), (u'SY', u'Syrian Arab Republic'), (u'TW', u'Taiwan (Province of China)'), (u'TJ', u'Tajikistan'), (u'TZ', u'Tanzania, United Republic of'), (u'TH', u'Thailand'), (u'TL', u'Timor-Leste'), (u'TG', u'Togo'), (u'TK', u'Tokelau'), (u'TO', u'Tonga'), (u'TT', u'Trinidad and Tobago'), (u'TN', u'Tunisia'), (u'TR', u'Turkey'), (u'TM', u'Turkmenistan'), (u'TC', u'Turks and Caicos Islands'), (u'TV', u'Tuvalu'), (u'UG', u'Uganda'), (u'UA', u'Ukraine'), (u'AE', u'United Arab Emirates'), (u'GB', u'United Kingdom'), (u'US', u'United States'), (u'UM', u'United States Minor Outlying Islands'), (u'UY', u'Uruguay'), (u'UZ', u'Uzbekistan'), (u'VU', u'Vanuatu'), (u'VE', u'Venezuela, Bolivarian Republic of'), (u'VN', u'Viet Nam'), (u'VG', u'Virgin Islands (British)'), (u'VI', u'Virgin Islands (U.S.)'), (u'WF', u'Wallis and Futuna'), (u'EH', u'Western Sahara'), (u'YE', u'Yemen'), (u'ZM', u'Zambia'), (u'ZW', u'Zimbabwe'), (u'AX', u'\xc5land Islands')])),
                ('phone', models.CharField(max_length=50)),
                ('avoid_problems', models.CommaSeparatedIntegerField(max_length=16, blank=True)),
                ('avoid_problems_other', models.CharField(max_length=50, blank=True)),
                ('match_request', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('unmatch_request', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
