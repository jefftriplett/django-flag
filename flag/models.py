from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from . import signals


STATUS = getattr(settings, "FLAG_STATUSES", [
    ("1", _("flagged")),
    ("2", _("flag rejected by moderator")),
    ("3", _("creator notified")),
    ("4", _("content removed by creator")),
    ("5", _("content removed by moderator")),
])


class FlaggedContent(models.Model):

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey("content_type", "object_id")

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="flagged_content")  # user who created flagged content -- this is kept in model so it outlives content
    status = models.CharField(max_length=1, choices=STATUS, default="1")
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name="moderated_content")  # moderator responsible for last status change
    count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [("content_type", "object_id")]


class FlagInstance(models.Model):

    flagged_content = models.ForeignKey(FlaggedContent)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)  # user flagging the content
    when_added = models.DateTimeField(default=timezone.now)
    when_recalled = models.DateTimeField(null=True)  # if recalled at all
    comment = models.TextField()  # comment by the flagger


def add_flag(flagger, content_type, object_id, content_creator, comment, status=None):

    # check if it's already been flagged
    defaults = dict(creator=content_creator)
    if status is not None:
        defaults["status"] = status
    flagged_content, created = FlaggedContent.objects.get_or_create(
        content_type=content_type,
        object_id=object_id,
        defaults=defaults
    )
    if not created:
        flagged_content.count = models.F("count") + 1
        flagged_content.save()
        # pull flagged_content from database to get count attribute filled
        # properly (not the best way, but works)
        flagged_content = FlaggedContent.objects.get(pk=flagged_content.pk)

    flag_instance = FlagInstance(
        flagged_content=flagged_content,
        user=flagger,
        comment=comment
    )
    flag_instance.save()

    signals.content_flagged.send(
        sender=FlaggedContent,
        flagged_content=flagged_content,
        flagged_instance=flag_instance,
    )

    return flag_instance
