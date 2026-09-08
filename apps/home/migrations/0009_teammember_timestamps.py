from django.db import migrations, models


class Migration(migrations.Migration):
    """Rename TeamMember.create_at -> updated_at, add a real created_at, order by name.

    Written by hand rather than generated: makemigrations cannot tell a rename
    from a drop-and-add without prompting, and answering "no" would delete the
    column and lose the timestamps.

    `create_at` was declared auto_now, so despite its name it always held the last
    modification time. TeamMemberSitemap published it as <lastmod>, which meant an
    unrelated admin edit looked to crawlers like a content change.
    """

    dependencies = [
        ('home', '0008_contactmessage'),
    ]

    operations = [
        migrations.RenameField(
            model_name='teammember',
            old_name='create_at',
            new_name='updated_at',
        ),
        migrations.AddField(
            model_name='teammember',
            # Nullable: existing rows have no true creation time and inventing one
            # would repeat the mistake this migration exists to fix.
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterModelOptions(
            name='teammember',
            options={'ordering': ['name']},
        ),
    ]
