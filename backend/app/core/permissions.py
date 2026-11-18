# add inside the existing permission enum:
SCHEDULES_MANAGE = "schedules:manage"

# add permission.SCHEDULES_MANAGE to the existing permission sets
# for HOD and department Admin.

# keep RESOURCES_REND for roles allowed to view schedules.
# Do not grant manage permission to other roles unless the project
# requirements explicitly authorize it.