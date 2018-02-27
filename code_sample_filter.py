class UniversitySchoolFilter(FilterSet):
    """
    University School Filter
    """
    university_id = django_filters.UUIDFilter(name="university_foreign_key__object_id")
    is_non_degree = django_filters.BooleanFilter(method="non_degree_filter")
    is_AMP = django_filters.BooleanFilter(name="nondegreecategory__nondegreecourse__is_advanced_management_program",
                                          distinct=True)
    client_id = django_filters.UUIDFilter(name="non_degree_user__id")

    class Meta:
        model = UniversitySchool
        fields = ['university_id', ]

    def non_degree_filter(self, queryset, name, value):
        if value is True:
            return queryset.filter(nondegreecategory__isnull=False).distinct()
        return queryset


class NonDegreeWhoopsReportFilter(FilterSet):
    """
    Non-Degree Whoops Report Filter
    """
    university_school = django_filters.UUIDFilter(name="university_school__object_id")
    client_id = django_filters.UUIDFilter(method="filter_client_id")

    class Meta:
        model = NonDegreeWhoopsReport
        fields = ['active', 'university_school', 'starred', 'completed', 'client_id', ]

    def filter_client_id(self, queryset, name, value):
        if not value:
            return queryset
        try:
            user = UniversityCustomer.objects.get(id=value)
        except ObjectDoesNotExist:
            return NonDegreeWhoopsReport.objects.none()
        queryset = queryset.filter(university_school=user.Ceeb).filter(active=True)
        return queryset


class MultipleSearchFilter(SearchFilter):
    """
    Multiple search Filter, for search fields with or relationship.
    For example:
    With data: aabbcc
    search key word: bb,dd,ff,gg,hh
    data 'aabbcc' will be reached
    """
    
    # The URL query parameter used for the search.
    search_param = 'multiple_search'

    search_title = _('Multiple Search')
    search_description = _('A multiple search term.')

    def filter_queryset(self, request, queryset, view):
        search_fields = getattr(view, 'multiple_search_fields', None)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(six.text_type(search_field))
            for search_field in search_fields
        ]

        base = queryset
        queries = []
        for search_term in search_terms:
            queries += [
                models.Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
        queryset = queryset.filter(reduce(operator.or_, queries))

        if self.must_call_distinct(queryset, search_fields):
            queryset = distinct(queryset, base)
        return queryset
