class AbstractDatedObject(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)

    class Meta:
        abstract = True
        default_permissions = ('add', 'change', 'delete', 'view_only')


class AbstractSimpleObject(AbstractDatedObject):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=40, null=False, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta(AbstractDatedObject.Meta):
        abstract = True
        ordering = [
            'name'
        ]

    def __str__(self):
        return "{0}".format(self.name)


class NonDegreeCategory(AbstractDatedObject):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, null=False)
    university_school = models.ForeignKey(UniversitySchool, on_delete=models.PROTECT)
    version = models.PositiveIntegerField(null=False, default=1)
    active = models.BooleanField(default=False)
    effective_date_start = models.DateTimeField(blank=True, null=True)
    effective_date_end = models.DateTimeField(blank=True, null=True)

    class Meta(AbstractDatedObject.Meta):
        ordering = [
            'name',
            '-version',
        ]

        unique_together = ('name', 'version', 'university_school')

        indexes = [
            models.Index(fields=['name', 'university_school', 'active']),
            models.Index(fields=['university_school']),
        ]

    def __str__(self):
        return "{0} - v{1} - {2}".format(self.name, self.version, self.university_school)


class NonDegreeCourse(AbstractDatedObject):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, null=False)
    university_school = models.ForeignKey(UniversitySchool, on_delete=models.PROTECT)
    category = models.ManyToManyField(NonDegreeCategory, blank=True, null=True)
    active = models.BooleanField(default=False)
    is_advanced_management_program = models.BooleanField(default=False)
    course_type = models.CharField(max_length=20, null=True, blank=True, choices=(("onsite", "On site"),
                                                                                  ("online", "Online"),
                                                                                  ("hybrid", "Hybrid"),))
    location_info = models.CharField(max_length=255, null=True, blank=True)
    tuition = models.CharField(max_length=255, null=True, blank=True)   # replaced by currency and tuition_number
    currency = models.ForeignKey(CurrencyRef, on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    tuition_number = models.PositiveIntegerField(blank=True, null=True, verbose_name='Tuition')
    tuition_note = models.TextField(blank=True, null=True)
    Repeatable = models.CharField(max_length=10, null=True, blank=True, choices=(("Y", "Yes"),
                                                                                 ("N", "No"),))
    version = models.PositiveIntegerField(null=False, default=1)
    effective_date_start = models.DateTimeField(blank=True, null=True)
    effective_date_end = models.DateTimeField(blank=True, null=True)

    class Meta(AbstractDatedObject.Meta):
        ordering = [
            'name',
            '-version',
        ]

        unique_together = ('name', 'version', 'university_school',)

        indexes = [
            models.Index(fields=['name', 'active', 'university_school']),
            models.Index(fields=['name', 'university_school', 'type']),
        ]

    def __str__(self):
        return "{0} - v{1} - {2}".format(self.name, self.version, self.university_school)


class NonDegreeCategoryURL(AbstractDatedObject):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.ForeignKey(NonDegreeUrlTypeRef, on_delete=models.PROTECT, related_name='+', null=False)
    note = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(max_length=1024, null=False)
    category = models.ForeignKey(NonDegreeCategory, on_delete=models.CASCADE, null=False)
    webpage = models.ForeignKey(WebPage, on_delete=models.SET_NULL, null=True)
    processed_scan = models.ForeignKey(WebPageScan, on_delete=models.SET_NULL, related_name='+', null=True)

    class Meta(AbstractDatedObject.Meta):
        ordering = [
            'type',
        ]
        unique_together = ('url', 'category')

    def __str__(self):
        return "{0}".format(self.url)


class NonDegreeCourseURL(AbstractDatedObject):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.ForeignKey(NonDegreeUrlTypeRef, on_delete=models.PROTECT, related_name='+', null=False)
    note = models.CharField(max_length=200, null=True, blank=True)
    url = models.URLField(max_length=1024, null=False)
    course = models.ForeignKey(NonDegreeCourse, on_delete=models.CASCADE, null=False)
    webpage = models.ForeignKey(WebPage, on_delete=models.SET_NULL, null=True)
    processed_scan = models.ForeignKey(WebPageScan, on_delete=models.SET_NULL, related_name='+', null=True)

    class Meta(AbstractDatedObject.Meta):
        ordering = [
            'type',
        ]
        unique_together = ('url', 'course')

    def __str__(self):
        return "{0}".format(self.url)


class NonDegreeCourseDate(AbstractDatedObject):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(NonDegreeCourse, on_delete=models.PROTECT)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    duration = models.PositiveIntegerField(blank=True, null=True)

    class Meta(AbstractDatedObject.Meta):
        ordering = [
            '-start_date',
        ]
        unique_together = ('course', 'start_date', 'end_date',)

    def __str__(self):
        return "{0}-{1}".format(self.start_date, self.end_date)
