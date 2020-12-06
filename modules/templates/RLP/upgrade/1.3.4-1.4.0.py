# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLP Template Version 1.3.4 => 1.4.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/upgrade/1.3.4-1.4.0.py
#
import sys
#from s3 import S3DateTime

#from gluon.storage import Storage
#from gluon.tools import callback
#from lxml import etree

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)

# Load models for tables
htable = s3db.hrm_human_resource
atable = s3db.pr_person_availability

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLP")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    bi = s3base.S3BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    with open(filename, "r") as File:
        try:
            bi.import_role(filename)
        except Exception as e:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Install new skills
#
if not failed:
    info("Install new skills")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "hrm", "skill.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "Demo", "hrm_skill.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("hrm_skill")
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        if resource.error:
            infoln("...failed")
            infoln(resource.error)
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Install new occupation types
#
if not failed:
    info("Install new occupation types")

    from gluon import IS_NOT_EMPTY, IS_LENGTH

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "pr", "occupation_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "pr_occupation_type.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("pr_occupation_type")
            ottable = resource.table
            field = ottable.name
            field.requires = [IS_NOT_EMPTY(), IS_LENGTH(128)]
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        if resource.error:
            infoln("...failed")
            infoln(resource.error)
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Add availability records for all volunteers
#
if not failed:
    info("Add availability records")

    # Get all volunteers without availability record
    query = (htable.type == 2) & \
            (htable.status == 1) & \
            (htable.deleted == False) & \
            (atable.id == None)
    left = atable.on((atable.person_id == htable.person_id) & \
                     (atable.deleted == False))
    rows = db(query).select(htable.person_id, left=left)

    # Create missing availability records
    created = 0
    for row in rows:
        info(".")
        data = {"person_id": row.person_id,
                "days_of_week": [0, 1, 2, 3, 4, 5, 6],
                }
        record_id = atable.insert(**availability)
        if record_id:
            created += 1
        data["id"] = record_id
        auth.s3_set_record_owner(atable, record_id)
        #s3db.onaccept(atable, data) # Run in next step anyway
    if created != len(rows):
        infoln("...failed")
        failed = True
    else:
        infoln("...done (%s records created)" % created)

# -----------------------------------------------------------------------------
# Upgrade availability records
#
if not failed:
    info("Upgrade availability records")

    query = (atable.deleted == False)
    rows = db(query).select(atable.id,
                            atable.person_id,
                            atable.schedule_json,
                            atable.schedule,
                            atable.comments,
                            )
    updated = 0
    for row in rows:
        # Move schedule contents into comments field
        if row.schedule and not row.comments:
            row.update_record(comments = row.schedule,
                              schedule = None,
                              )
        # Run onaccept to generate rules and populate days_of_week
        s3db.onaccept(atable, row, method="update")
        updated += 1

    infoln("...done (%s records upgraded)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
