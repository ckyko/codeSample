class SaveFormsetMixin(object):
    def save_formset(self, request, form, formset, change):
        """
        Automatically create or delete WebPage for webtracking
        """
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            if isinstance(obj, NonDegreeCourseURL) or isinstance(obj, NonDegreeCategoryURL):
                category_urls = NonDegreeCategoryURL.objects.filter(url=obj.url)
                course_urls = NonDegreeCourseURL.objects.filter(url=obj.url)
                program_urls = WebPageProgramMap.objects.filter(webpage__url=obj.url)
                len_of_category_urls = category_urls.count()
                len_of_course_urls = course_urls.count()
                len_of_program_urls = program_urls.count()
                if len_of_category_urls + len_of_course_urls + len_of_program_urls == 1:
                    try:
                        web_page = WebPage.objects.get(url=obj.url)
                    except WebPage.DoesNotExist:
                        web_page = None
                    if web_page is not None:
                        web_page.delete()
            obj.delete()
        for instance in instances:
            if isinstance(instance, NonDegreeCourseURL) or isinstance(instance, NonDegreeCategoryURL):
                web_page, created = WebPage.objects.get_or_create(url=instance.url)
                instance.webpage = web_page
            instance.save()
        formset.save_m2m()


class NonDegreeCourseAdmin(SaveFormsetMixin, AutoUserModelAdmin):
    save_as = True

    inlines = [
        NonDegreeCourseDateInline,
        NonDegreeCourseURLInline,
    ]
    readonly_fields = ('object_id', 'date_created', 'date_modified', 'created_by', 'modified_by')

    list_display = ('name', 'university_school', 'active', 'version', 'type', 'date_created', 'date_modified',
                    'created_by', 'modified_by')
    list_filter = ('active', 'version', 'type', 'Repeatable', 'date_created', 'date_modified', 'created_by',
                   'modified_by',)

    filter_horizontal = ('category',)
    ordering = ('-version', 'name',)

    search_fields = [
        'name',
        'university_school__ceeb',
        'university_school__school',
        'university_school__university_foreign_key__name',
    ]

    fieldsets = [
        ('Management Record', {
            'classes': ('collapse',),
            'fields': [
                'object_id',
                ('date_created', 'created_by'),
                ('date_modified', 'modified_by'),
            ]
        }),
        ('Course Identity', {
            'classes': ('collapse', 'open'),
            'fields': [
                'name',
                'university_school',
                'category',
                'active',
                'is_advanced_management_program',
                'version',
                'type',
                'location_info',
                'tuition',
                ('currency', 'tuition_number'),
                'tuition_note',
                'Repeatable',
                'effective_date_start',
                'effective_date_end',
            ]
        }),
    ]

    class Media:
        js = ("js/admin/open_new_tab.js",)


class ProgramAdmin(AutoUserModelAdmin):
    save_as = True
    form = select2_modelform(Program, attrs={'width': '500px'})
    change_form_template = 'admin/ceeb_program/program/change_form.html'

    inlines = [
        DurationInline,
        CurriculumInline,
        TuitionInline,
        DeadlineInline,
        RequirementInline,
        ScholarshipInline,
        AdditionalNoteInline,
    ]

    readonly_fields = ('object_id', 'date_created', 'date_modified', 'created_by', 'modified_by', 'assignee',
                       'reviewer', 'assigner', 'assignment_status', 'need_update_notes', 'review_status', 'review_link',
                       'degree_master')

    list_display = ('object_id', 'ceeb_code', 'program_name', 'degree_name', 'degree_master', 'department',
                    #'date_created',
                    'date_modified', 'created_by', 'modified_by', 'assignee', 'assignment_status', 'reviewer',
                    'review_status')
    list_display_links = ('object_id',)

    list_filter = ('date_modified', 'discontinued', 'created_by', 'modified_by', 'degree__master')

    tracking_url_fields = ['url', 'homepage_url', 'additional_url', 'parent_handbook_url', 'program_faq_url',
                           'stats_profile_url', 'admission_stats_parent_url', 'job_placement_url',
                           'job_placement_parent_url', 'part_time_url', 'nitty_gritty_degree_duration_program_url',
                           'curriculum_url', 'transfer_unit_url', 'thesis_url', 'dissertation_url',
                           'university_cost_url', 'school_cost_url', 'deadline_url', 'program_req_url',
                           'school_req_url', 'intl_req_url', 'scholarship_program_specific_url',
                           'scholarship_general_url']
    search_fields = [
        'object_id',
        'university_school__ceeb',
        'university_school__university_foreign_key__name',
        'program_name',
        'degree__name',
        'subject__name',
        'department',
    ]

    filter_horizontal = ('subject', 'same_as_many', 'sub_subject',)

    fieldsets = [
        ('Program Management Record', {
            'classes': ('collapse',),
            'fields': [
                'object_id',
                ('date_created', 'created_by'),
                ('date_modified', 'modified_by'),
                'assignee',
                ('assignment_status', 'assigner'),
                'need_update_notes',
                'reviewer',
                'review_status',
                'review_link',
            ]
        }),
        ('Program Identity', {
            'classes': ('collapse', 'open'),
            'fields': [
                'university_school',
                'program_name',
                'degree',
            ]
        }),
        ('Program Details', {
            'classes': ('collapse', 'open'),
            'fields': [
                'department',
                'subject',
                'sub_subject',
                'specialization',
                'highlights',
                'audience',
                'certification',
                'job_placement',
                'discontinued',
                'misc',
                'same_as_many',
                'online_program',
                'terminal_or_fs_degree',
            ]
        }),
        ('URLs', {
            'classes': ('collapse', 'open'),
            'fields': [
                'url',
                'homepage_url',
                'additional_url',
                'parent_handbook_url',
                'program_faq_url',
                'stats_profile_url',
                'admission_stats_parent_url',
                'job_placement_url',
                'job_placement_parent_url',
            ]
        }),
    ]

    actions = ['set_update_action']

    def set_update_action(self, request, queryset):
        """
        This is update action function.
        The attributes that we need batch updated are in the forms.py
        """

        # permission checking
        if not request.user.groups.filter(name=GROUP_CAN_BATCH_UPDATE):
            messages.error(request, "Permission denied!")
            return

        def batch_update_save(table_change, attrs_list, saved_form, updated_attributes):
            for attribute in attrs_list:
                if attribute in request.POST:
                    new_value = saved_form.cleaned_data[attribute]
                    setattr(table_change, attribute, new_value)
                    table_change.save()
                    updated_attributes.append(attribute)

        form_name_dict = {'program_form': 'program',
                          'duration_form': 'duration',
                          'curriculum_form': 'curriculum',
                          'tuition_form': 'tuition',
                          'deadline_form': 'deadline',
                          'requirement_form': 'requirement',
                          'scholarship_form': 'scholarship', }
        form_dict = {'program_form': ProgramForm,
                     'duration_form': DurationForm,
                     'curriculum_form': CurriculumForm,
                     'tuition_form': TuitionForm,
                     'deadline_form': DeadlineForm,
                     'requirement_form': RequirementForm,
                     'scholarship_form': ScholarshipForm, }
        form_attrs_dict = {'program_form': BATCH_UPDATE_PROGRAM,
                           'duration_form': BATCH_UPDATE_DURATION,
                           'curriculum_form': BATCH_UPDATE_CURRICULUM,
                           'tuition_form': BATCH_UPDATE_TUITION,
                           'deadline_form': BATCH_UPDATE_DEADLINE,
                           'requirement_form': BATCH_UPDATE_REQUIREMENT,
                           'scholarship_form': BATCH_UPDATE_SCHOLARSHIP, }

        data = {'title': u'Update',
                'objects': queryset}

        # displaying 'table not created' error.
        error_message_list = []
        for program in queryset:
            not_created_forms = []
            for form_name, table_name in form_name_dict.items():
                if (not hasattr(program, table_name)) and table_name != 'program':
                    not_created_forms.append(table_name)
            if not_created_forms:
                error_message = 'For program {0}, can not update: {1}. Please create them first.'\
                    .format(program.object_id, ", ".join(not_created_forms))
                error_message_list.append(error_message)
        data['error_message_list'] = error_message_list

        # displaying selecting form
        if 'select_action' in request.POST:
            for form_name, form in form_dict.items():
                if request.POST.get(form_name, '') == form_name:
                    data[form_name] = form()

        # save data to all program
        elif 'save' in request.POST:
            for program in queryset:
                updated_forms = []
                not_updated_forms = []
                updated_attrs = []
                for form_name, form in form_dict.items():
                    if request.POST.get(form_name) == form_name:
                        save_form = form(request.POST)
                        if form_name == "program_form" and save_form.is_valid():
                            table = program
                            batch_update_save(table, form_attrs_dict[form_name], save_form, updated_attrs)
                            updated_forms.append(form_name_dict[form_name])
                        elif hasattr(program, form_name_dict[form_name]) and save_form.is_valid():
                            table = getattr(program, form_name_dict[form_name])
                            batch_update_save(table, form_attrs_dict[form_name], save_form, updated_attrs)
                            updated_forms.append(form_name_dict[form_name])
                        else:
                            not_updated_forms.append(form_name_dict[form_name])

                # update program's date_modified and modified_by, and add batch update information to history.
                if updated_attrs:
                    program.modified_by = request.user
                    program.date_modified = datetime.now()
                    program.save()
                    history_message = "batch update: {0}".format(", ".join(updated_attrs))
                    LogEntry.objects.log_action(
                        user_id=request.user.id,
                        content_type_id=ContentType.objects.get_for_model(program).pk,
                        object_id=program.pk,
                        object_repr=force_text(program),
                        action_flag=CHANGE,
                        change_message=history_message)

                # displaying success or error messages.
                update_str = 'For program {0}, updated: {1}'.format(program.object_id, ", ".join(updated_forms))
                messages.success(request, update_str)
                if not_updated_forms:
                    not_update_str = 'For program {0}, can not update: {1}. Please create them first.'\
                        .format(program.object_id, ", ".join(not_updated_forms))
                    messages.error(request, not_update_str)
            return

        # return confirmation page which showing all programs.
        elif 'confirmation' in request.POST:
            form_edited = {}
            save_attrs = {}
            for form_name, form in form_dict.items():
                if request.POST.get(form_name) == form_name:
                    form_edited[form_name] = form(request.POST)
                    for attr in form_attrs_dict[form_name]:
                        save_attrs[attr] = request.POST.get(attr + '_save', '')
            data['save_attrs'] = save_attrs

            for program in queryset:
                for form_name, form in form_edited.items():
                    for field in form:
                        if save_attrs[field.name] != 'save':
                            field.save = False
                        else:
                            field.save = True

                    setattr(program, form_name, form)  # add new form to program

                    # add old form to program for displaying old data.
                    if form_name == "program_form":
                        old_table = program
                        old_form = form_dict[form_name](instance=old_table)
                        for field in old_form:
                            if save_attrs[field.name] != 'save':
                                field.save = False
                            else:
                                field.save = True

                    elif hasattr(program, form_name_dict[form_name]):
                        old_table = getattr(program, form_name_dict[form_name])
                        old_form = form_dict[form_name](instance=old_table)
                        for field in old_form:
                            if save_attrs[field.name] != 'save':
                                field.save = False
                            else:
                                field.save = True
                    else:
                        old_form = None

                    setattr(program, form_name+'_original', old_form)

            return render(request, 'admin/ceeb_program/batch_update_confirmation.html', data)

        else:
            data['choose_form'] = True

        return render(request, 'admin/ceeb_program/action_program.html', data)

    set_update_action.short_description = u'Update selected programs'

    def ceeb_code(self, obj):
        return obj.university_school.ceeb

    def degree_name(self, obj):
        return obj.degree.name

    def degree_master(self, obj):
        return obj.degree.master

    def assignee(self, obj):
        assignment = ProgramAssignment.objects.get(program=obj)
        return assignment.assignee

    def reviewer(self, obj):
        proof = ProgramProof.objects.get(program=obj)
        return proof.reviewer

    def assignment_status(self, obj):
        assignment = ProgramAssignment.objects.get(program=obj)
        return assignment.status

    def need_update_notes(self, obj):
        assignment = ProgramAssignment.objects.get(program=obj)
        return assignment.need_update_notes

    def review_status(self, obj):
        proof = ProgramProof.objects.get(program=obj)
        return proof.status

    def assigner(self, obj):
        assignment = ProgramAssignment.objects.get(program=obj)
        return assignment.modified_by

    def review_assigner(self, obj):
        assignment = ProgramProof.objects.get(program=obj)
        return assignment.modified_by

    def review_link(self, obj):
        proof = ProgramProof.objects.get_or_create(program=obj)[0]
        return format_html('<a href="/ceeb-admin/record_management/programproof/{0}/change">Update review</a>',
                           proof.object_id)

    ceeb_code.admin_order_field = 'university_school__ceeb'
    degree_name.admin_order_field = 'degree'

    def get_inline_instances(self, request, obj=None):
        """
        In this function, we return all inline_instances if user has either change, add or delete permission
        for main object.
        In the original function, it check if user has either change, add or delete models permission for
        inline objects. But we don't want to give inline's models permission to some group of user. So we
        only check main object's permission.

        :param request:
        :param obj:
        :return: A list of inline instance
        """
        inline_instances = []
        if self.has_change_permission(request, obj) or self.has_add_permission(request) or \
           self.has_delete_permission(request, obj):
            for inline_class in self.inlines:
                inline = inline_class(self.model, self.admin_site)
                inline_instances.append(inline)
        return inline_instances

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if request.user.groups.filter(name=GROUP_PROOF_EXPERTS).count():
            extra_context['proof_experts'] = True
        if request.user.groups.filter(name=GROUP_KNOWLEDGE_EXPERTS).count()\
                or request.user.groups.filter(name=GROUP_KE_VENDORS).count():
            extra_context['knowledge_experts'] = True
        return super(ProgramAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def add_url_to_web_tracking(self, obj, form_data):
        url_list = []
        for url_name in self.tracking_url_fields:
            if url_name in form_data.keys():
                url = form_data[url_name]
                if url:
                    url_list.append("(uuid_generate_v4(), '{date_created}', '{date_modified}', {revision}, '{url}', "
                                    "{enabled}, {fetch_error_count})"
                                    .format(date_created=datetime.utcnow().strftime(TIME_FORMAT),
                                            date_modified=datetime.utcnow().strftime(TIME_FORMAT),
                                            revision=0,
                                            url=url,
                                            enabled=True,
                                            fetch_error_count=0))
        if url_list:
            value = ','.join(url_list)
            with connection.cursor() as cursor:
                cursor.execute("""
                        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                        INSERT INTO "webtracking_webpage"
                            ("object_id", "date_created", "date_modified", "revision", "url", "enabled",
                            "fetch_error_count")
                            VALUES
                            {value}
                            ON CONFLICT DO NOTHING;
                        """.format(value=value))

    def save_formset(self, request, form, formset, change):
        index = 0
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.save()
            if formset.is_valid():
                self.add_url_to_web_tracking(obj=instance.program, form_data=formset.cleaned_data[index])
            index += 1
        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        if change and form.is_valid():
            self.add_url_to_web_tracking(obj=obj, form_data=form.cleaned_data)

        try:
            program_assignment = ProgramAssignment.objects.get(program=obj)
        except ObjectDoesNotExist:
            program_assignment = None

        try:
            program_proof = ProgramProof.objects.get(program=obj)
        except ObjectDoesNotExist:
            program_proof = None

        # auto update assignment status
        if program_assignment:
            if program_assignment.assignee == request.user and program_assignment.status == 'Assigned':
                ProgramAssignment.objects.update_or_create(program=obj, defaults={'status': 'InProgress'})

            assignment_status = request.POST.get('assignment_status', '')  # get assignment_status
            if assignment_status and self.has_change_permission(request, obj):
                if program_assignment.assignee == request.user or program_proof.reviewer == request.user:
                    # update assignee status
                    ProgramAssignment.objects.update_or_create(program=obj, defaults={'status': assignment_status})
                    if assignment_status == 'Done':
                        remove_perm('ceeb_program.change_program', request.user, obj)  # remove permission from assignee
                        audit_logger.info('{0} lost modification permission by finishing assignment of program {1}:{2}'
                                          .format(request.user.username, obj.object_id, obj))
                        email_message = "Assignee finished assignment: \n{0}{1} \nAssignee: {2}\nEmail: {3}"\
                                        .format(get_current_site(request), settings.PROGRAM_URL.format(obj.object_id),
                                                program_assignment.assignee.username, program_assignment.assignee.email)
                        send_email(request, 'Assignee finished assignment', email_message,
                                   [program_proof.reviewer.email])

                    if assignment_status == "NeedUpdate":  # if assignment need update
                        old_assignee = program_assignment.assignee
                        assign_perm('ceeb_program.change_program', old_assignee, obj)  # assign permission to assignee
                        audit_logger.info('{0} granted modification permission to {1} for assignment follow up, '
                                          'for program {2}:{3}.'
                                          .format(request.user.username, old_assignee.username, obj.object_id, obj))
                        email_message = "Received need-update assignment: \n{0}{1} \n"\
                                        .format(get_current_site(request),  settings.PROGRAM_URL.format(obj.object_id))
                        need_update_note = request.POST.get('need_update_note', '')  # get need_update_note

                        # if there is need update note, send email to assignee
                        if need_update_note:
                            ProgramAssignment.objects.update_or_create(program=obj,
                                                                       defaults={'need_update_notes': need_update_note})
                            email_message += "Need update note: {0}\n".format(need_update_note)
                        email_message += "Assigned by: {0}\nEmail: {1}".format(request.user.username,
                                                                               request.user.email)
                        send_email(request, 'Assignment Need Update', email_message, [old_assignee.email])
                else:
                    messages.add_message(request, messages.ERROR,
                                         "Only assignee or reviewer can update assignment status.")

        # auto update review status
        if program_proof:
            if program_proof.reviewer == request.user and program_proof.status == 'Assigned':
                ProgramProof.objects.update_or_create(program=obj, defaults={'status': 'InProgress'})

            review_status = request.POST.get('review_status', '')  # get review_status
            if review_status and self.has_change_permission(request, obj):
                if program_proof.reviewer == request.user:
                    # update reviewer status
                    ProgramProof.objects.update_or_create(program=obj, defaults={'status': review_status})
                else:
                    messages.add_message(request, messages.ERROR, "Only reviewer can update review status.")

        super(ProgramAdmin, self).save_model(request, obj, form, change)
        if program_assignment is None:
            ProgramAssignment.objects.create(program=obj, status='None')
        if program_proof is None:
            ProgramProof.objects.create(program=obj, status='None')
        return