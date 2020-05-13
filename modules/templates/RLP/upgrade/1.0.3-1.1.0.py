# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLP Template Version 1.0.3 => 1.1.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/upgrade/1.0.3-1.1.0.py
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
    info("Assign NOTES_EDITOR role to COORDINATORs")

    auth = current.auth

    gtable = auth.settings.table_group
    mtable = auth.settings.table_membership
    updated = 0
    if gtable is not None:
        query = (gtable.uuid == "COORDINATOR") & \
                (gtable.id == mtable.group_id) & \
                (mtable.deleted == False)
        rows = db(query).select(mtable.user_id,
                                groupby = mtable.user_id,
                                )
        for row in rows:
            info(".")
            auth.s3_assign_role(row.user_id, "NOTES_EDITOR")
            updated += 1

    infoln("...done (%s users assigned)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
