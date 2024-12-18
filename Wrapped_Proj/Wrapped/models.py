from django.db import models
from django.db import transaction
from django.contrib.auth.models import User

class Wrap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=255)
    timeframe = models.CharField(max_length=50)
    generated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

class WrapCounter(models.Model):
    current_wrap_id = models.PositiveIntegerField(default=1)

    @classmethod
    def get_next_wrap_id(cls):
        """Fetches the next unique wrap_id and increments the counter."""
        # Ensure that the counter exists and create it if it doesn't
        counter, created = cls.objects.get_or_create(id=1)
        next_wrap_id = counter.current_wrap_id
        counter.current_wrap_id += 1
        counter.save()
        return next_wrap_id


class UserWrappedHistory(models.Model):
    creator_name = models.CharField(max_length=255, default='Unknown')

    top_artists = models.JSONField(default=list)
    top_tracks = models.JSONField(default=list)
    top_genres = models.JSONField(default=list)
    playlists = models.JSONField(default=list)

    # Other fields
    country = models.CharField(max_length=100, default='Unknown')
    image_url = models.URLField(max_length=500, null=True, blank=True)
    followers = models.IntegerField(default=0)

    # Popularity metrics
    top_track_popularity_score = models.FloatField(default=0)
    top_track_popularity_message = models.TextField(null=True, blank=True)

    # Optional fields
    recently_played = models.JSONField(default=list, null=True, blank=True)
    saved_albums = models.JSONField(default=list, null=True, blank=True)

    user_id = models.CharField(max_length=255, unique=False)  # User identifier
    public = models.BooleanField(default=False)

    SHORT_TERM = 'short_term'
    MEDIUM_TERM = 'medium_term'
    LONG_TERM = 'long_term'

    TIMEFRAME_CHOICES = [
        (SHORT_TERM, 'Short Term'),
        (MEDIUM_TERM, 'Medium Term'),
        (LONG_TERM, 'Long Term'),
    ]

    timeframe = models.CharField(
        max_length=50,
        choices=TIMEFRAME_CHOICES,
    )

    wrap_id = models.PositiveIntegerField(null=True, blank=True)  # Wrap ID (no longer unique=True)

    display_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="A user-friendly name for the wrap."
    )  # New field to store the display name

    def save(self, *args, **kwargs):
        if not self.wrap_id:
            # We ensure that the wrap_id is unique for the user_id and timeframe combination
            while True:
                self.wrap_id = WrapCounter.get_next_wrap_id()

                # Check if this wrap_id already exists for the user_id and timeframe combination
                if not UserWrappedHistory.objects.filter(user_id=self.user_id, timeframe=self.timeframe, wrap_id=self.wrap_id).exists():
                    break  # If the wrap_id doesn't exist, break out of the loop

        # Set a default display_name if it is not provided
        if not self.display_name:
            self.display_name = f"{self.timeframe.replace('_', ' ').title()}"

        super().save(*args, **kwargs)

    generated_on = models.DateTimeField(auto_now_add=True)  # Store the date and time when created

    def __str__(self):
        return f"Wrapped for {self.user_id} in {self.timeframe} generated at {self.generated_on} with ID {self.wrap_id}"

    class Meta:
        unique_together = ('user_id', 'timeframe', 'wrap_id')  # Unique combination of user_id, timeframe, and wrap_id