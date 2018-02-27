class UniversitySchoolListSerializer(ModelSerializer):
    """
    University SchoolList Serializer
    """
    university = SerializerMethodField()
    non_degree_client = SerializerMethodField()

    class Meta:
        model = UniversitySchool
        fields = ('object_id', 'ceeb', 'school', 'university', 'non_degree_client')

    def get_university(self, obj):
        return obj.university_foreign_key.name

    def get_non_degree_client(self, obj):
        university_customers = obj.non_degree_user.all()
        university_customers = university_customers.filter(is_demo=False)
        return UniversityCustomerSerializer(university_customers, many=True).data


class UniversitySchoolDetailSerializer(ModelSerializer):
    """
    University school detail serializer
    """
    university = SerializerMethodField()
    categories = SerializerMethodField()

    class Meta:
        model = UniversitySchool
        fields = ('object_id', 'ceeb', 'school', 'university', 'categories',)

    def get_university(self, obj):
        return obj.university_foreign_key.name

    def get_categories(self, obj):
        categories = NonDegreeCategory.objects.filter(university_school=obj).filter(active=True)
        return CategorySerializer(categories, many=True).data


class NonDegreeReportListSerializer(ModelSerializer):
    """
    Non-degree report list serializer
    """
    school_name = SerializerMethodField()
    university_name = SerializerMethodField()

    class Meta:
        model = NonDegreeReport
        fields = ('object_id', 'school_name', 'university_name', 'school', 'date_created', 'categories', 'active',)

    def get_school_name(self, obj):
        return obj.school.school

    def get_university_name(self, obj):
        return obj.school.university_foreign_key.name


class WebPageListSerializer(ModelSerializer):
    """
    Web page list serializer
    """

    class Meta:
        model = WebPage
        fields = ('object_id', 'url', 'last_check_date', 'last_change_date', )


class AMPReportDetailSerializer(ModelSerializer):
    """
    AMP report detail serializer
    """
    webpage = SerializerMethodField()
    start_scan = SerializerMethodField()
    end_scan = SerializerMethodField()
    last_report_date_created = SerializerMethodField()

    class Meta:
        model = NonDegreeAMPReport
        fields = ('webpage', 'start_scan', 'end_scan', 'date_created', 'last_report_date_created',)

    def get_webpage(self, obj):
        web_page = obj.webpage
        return WebPageSerializer(web_page).data

    def get_start_scan(self, obj):
        start_scan = getattr(obj, 'start_scan', None)
        if start_scan is not None:
            return WebPageScanDetailSerializer(start_scan).data
        return None

    def get_end_scan(self, obj):
        end_scan = getattr(obj, 'end_scan', None)
        if end_scan is not None:
            return WebPageScanDetailSerializer(end_scan).data
        return None

    def get_last_report_date_created(self, obj):
        reports = NonDegreeAMPReport.objects.filter(webpage=obj.webpage).filter(date_created__lt=obj.date_created)\
                                            .order_by('-date_created')
        if reports:
            return reports.first().date_created
        return None
