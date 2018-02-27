class UniversitySchoolListAPI(PermissionMixin, ListAPIView):
    """
    Get list of user university school API
    """
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    serializer_class = UniversitySchoolListSerializer
    pagination_class = UniversitySchoolPagination
    filter_class = UniversitySchoolFilter

    search_fields = ('ceeb', 'school', 'university_foreign_key__name',)
    ordering_fields = ('ceeb', 'school', 'num_university_costomers', )
    ordering = ('ceeb', 'school', )      # default ordering

    def get_queryset(self, *args, **kwargs):
        if self.is_manager():
            university_schools = UniversitySchool.objects.all()\
                .annotate(num_university_costomers=Count('non_degree_user'))
        else:
            university_schools = UniversitySchool.objects.filter(non_degree_user=self.request.user)\
                .annotate(num_university_costomers=Count('non_degree_user'))
        return university_schools


class ReportCreateListAPI(PermissionMixin, CreateModelMixin, ListAPIView):
    """
    Get list of user non-degree report API & Create non-degree report API
    """
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    pagination_class = ReportPagination
    filter_class = ReportFilter

    search_fields = ('school__school', 'school__ceeb',)
    ordering_fields = ('school', 'date_created')
    ordering = ('school', '-date_created')      # default ordering

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ReportListSerializer
        else:
            return ReportCreateSerializer

    def get_queryset(self, *args, **kwargs):
        if self.is_manager():
            reports = NonDegreeReport.objects.all()
        else:
            reports = NonDegreeReport.objects \
                .filter(school__non_degree_user=self.request.user)
        return reports

    @staticmethod
    def create_report(request):
        if 'school' not in request.data:
            raise ValidationError("School object_id is required.")
        try:
            school = UniversitySchool.objects.get(object_id=request.data['school'])
        except UniversitySchool.DoesNotExist:
            raise ValidationError("Can not find school with this object_id.")

        categories = NonDegreeCategory.objects.filter(university_school=school).filter(active=True)
        data = JSONRenderer().render(CategorySerializer(categories, many=True).data)
        return data

    def create(self, request, *args, **kwargs):
        if not self.is_manager():
            return Response({"Failed": "Permission Denied!"}, status=HTTP_403_FORBIDDEN)

        data = request.POST.copy()
        data['categories'] = self.create_report(request)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        headers = self.get_success_headers(serializer.data)
        customers = UniversityCustomer.objects.filter(non_degree_schools=report.school)
        for customer in customers:
            NonDegreeReportCustomerMapping.objects.create(report=report, customer=customer)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class NonDegreeReportAPI(PermissionMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView):
    """
    Retrieve update and destroy non-degree Report API
    """
    lookup_field = 'object_id'

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return ReportUpdateSerializer
        else:
            return ReportSerializer

    def get_queryset(self, *args, **kwargs):
        if self.is_manager():
            reports = NonDegreeReport.objects.all()
        else:
            reports = NonDegreeReport.objects \
                .filter(school__non_degree_user=self.request.user)
        return reports

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if not self.is_manager():
            return Response({"Failed": "Permission Denied!"}, status=HTTP_403_FORBIDDEN)
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if not self.is_manager():
            return Response({"Failed": "Permission Denied!"}, status=HTTP_403_FORBIDDEN)
        return self.destroy(request, *args, **kwargs)


class NonDegreeCourseAPI(PermissionMixin, ListModelMixin, GenericAPIView):
    """
    Get list of user courses API
    """
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter, MultipleSearchFilter)
    serializer_class = CourseSerializer
    pagination_class = BasePagination
    filter_class = CourseFilter

    search_fields = ('name', )
    multiple_search_fields = ('name', )
    ordering_fields = ('name', 'university_school__school',)
    ordering = ('university_school__school', 'name', )      # default ordering

    def get_queryset(self, *args, **kwargs):
        courses = NonDegreeCourse.objects.filter(active=True)
        if not self.is_manager():
            courses = courses.filter(university_school__non_degree_user=self.request.user)
        return courses

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
