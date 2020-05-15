# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLP Template Version 1.1.0 => 1.1.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/upgrade/1.1.0-1.1.1.py
#
import datetime
import sys
#from s3 import S3DateTime

#from gluon.storage import Storage
#from gluon.tools import callback

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
dtable = s3db.hrm_delegation

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
if not failed:
    info("Clean up duplicate person details")

    dtable = s3db.pr_person_details
    query = (dtable.deleted == False)

    # Find all persons with duplicate person details
    rows = db(query).select(dtable.person_id.min(),
                            groupby = dtable.person_id,
                            having = dtable.id.count() > 1,
                            )
    updated = 0
    deleted = 0
    for row in rows:
        person_id = row[dtable.person_id.min()]

        query = (dtable.person_id == person_id) & \
                (dtable.deleted == False)
        details = db(query).select(dtable.id,
                                   dtable.alias,
                                   dtable.occupation,
                                   orderby = dtable.modified_on,
                                   )
        data = {}
        original = None
        for index, subrow in enumerate(details):
            if subrow.alias:
                data["alias"] = subrow.alias
            if subrow.occupation and "occupation" not in data:
                data["occupation"] = subrow.occupation
            if index == 0:
                original = subrow
            else:
                subrow.delete_record()
                deleted += 1
        if original:
            data["modified_on"] = dtable.modified_on
            data["modified_by"] = dtable.modified_by
            original.update_record(**data)
            updated += 1

    infoln("...done (%s records updated, %s record deleted)" % (updated, deleted))

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
