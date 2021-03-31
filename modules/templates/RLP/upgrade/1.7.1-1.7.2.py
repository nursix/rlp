# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLP Template Version 1.7.1 => 1.7.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/upgrade/1.7.1-1.7.2.py
#
import sys
#from s3 import S3Duplicate

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
atable = s3db.pr_person_availability

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLP")

# -----------------------------------------------------------------------------
# Migrate to pr_person_availability.weekly
#
if not failed:
    info("Migrate weekly availability")

    query = (atable.deleted == False)
    rows = db(query).select(atable.id,
                            atable.days_of_week,
                            )
    for row in rows:
        days = row.days_of_week
        weekly = sum(2**d for d in days)
        row.update_record(weekly = weekly,
                          modified_on = atable.modified_on,
                          modified_by = atable.modified_by,
                          )
    infoln("...done (%s records updated)" % len(rows))

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
