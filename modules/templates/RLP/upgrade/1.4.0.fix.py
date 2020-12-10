# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# Execute in web2py folder like:
# python web2py.py -S eden -M -R 1.4.0.fix.py
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
atable = s3db.pr_person_availability
ptable = s3db.pr_person
ltable = s3db.pr_person_user

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLP")

# -----------------------------------------------------------------------------
# Fix availability record ownerships
#
if not failed:
    info("Fix ownerships of availability records")

    left = [ptable.on(ptable.id == atable.person_id),
            ltable.on(ltable.pe_id == ptable.pe_id),
            ]
    query = (atable.owned_by_user == None) & \
            (atable.deleted == False)
    rows = db(query).select(atable.id,
                            ltable.user_id,
                            left = left,
                            )
    updated = 0
    for row in rows:
        record_id = row.pr_person_availability.id
        user_id = row.pr_person_user.user_id
        if not user_id:
            continue
        success = db(atable.id == record_id).update(owned_by_user = user_id,
                                                    modified_on = atable.modified_on,
                                                    modified_by = atable.modified_by,
                                                    )
        if success:
            updated += 1
    infoln("...done (%s records fixed)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
