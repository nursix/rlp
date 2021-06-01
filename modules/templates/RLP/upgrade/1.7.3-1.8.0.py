# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLP Template Version 1.7.3 => 1.8.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/upgrade/1.7.3-1.8.0.py
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
otable = s3db.org_organisation
utable = s3db.auth_user
ptable = s3db.pr_person
ltable = s3db.pr_person_user
ctable = s3db.pr_contact

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "RLP")

# -----------------------------------------------------------------------------
# Rename MSAGD=>MWG
#
if not failed:
    info("Rename MSAGD=>MWG")

    MSAGD = "Ministerium für Soziales, Arbeit, Gesundheit und Demografie"
    from templates.RLP.config import MWG

    # Get the Organisation
    query = (otable.name == MSAGD) & (otable.deleted == False)
    org = db(query).select(otable.id,
                           limitby = (0, 1),
                           ).first()
    if org:
        success = org.update_record(name = MWG,
                                    acronym = "MWG",
                                    website = "https://mwg.rlp.de",
                                    )
        if success:
            infoln("...done")
        else:
            infoln("...failed")
            failed = True
    else:
        infoln("...MSAGD Organisation not found (skip)")

# -----------------------------------------------------------------------------
# Fix demo accounts (demo only)
#
if not failed:
    info("Fix demo accounts")

    updated = 0

    query = (utable.email == "msagd_coordinator@example.com")
    user = db(query).select(utable.id, limitby=(0, 1)).first()
    if user:
        user.update_record(first_name = "MWG",
                           email = "mwg_coordinator@example.com",
                           )
        info(".")
        updated += 1

        query = (ltable.user_id == user.id) & \
                (ptable.pe_id == ltable.pe_id) & \
                (ltable.deleted == False)
        person = db(query).select(ptable.id, limitby=(0, 1)).first()
        if person:
            person.update_record(first_name = "MWG")
            info(".")
            updated += 1

        query = (ctable.value == "msagd_coordinator@example.com")
        contacts = db(query).select(ctable.id)
        for contact in contacts:
            contact.update_record(value="mwg_coordinator@example.com")
            info(".")
            updated += 1

        infoln("...done (%s records updated)" % updated)
    else:
        infoln("...not present (skip)")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")
