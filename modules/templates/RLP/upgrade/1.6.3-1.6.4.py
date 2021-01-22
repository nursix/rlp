# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLP Template Version 1.6.3 => 1.6.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/upgrade/1.6.3-1.6.4.py
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
ltable = s3db.pr_person_availability_site

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLP")

# -----------------------------------------------------------------------------
# Update realm entities for availability-site links
#
if not failed:
    info("Fix availability-site ownership")

    auth.set_realm_entity(table, (table.deleted == False), force_update=True)
    infoln("...done")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
