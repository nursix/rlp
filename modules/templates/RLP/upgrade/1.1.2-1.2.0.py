# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# RLP Template Version 1.1.2 => 1.2.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/RLP/upgrade/1.1.2-1.2.0.py
#
import datetime
import sys
#from s3 import S3DateTime

#from gluon.storage import Storage
#from gluon.tools import callback
from lxml import etree

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
stable = s3db.hrm_skill
ltable = s3db.hrm_competency
htable = s3db.hrm_human_resource
ptable = s3db.pr_person

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
# Install consent options (unless SHARE processing type already in DB)
#
if not failed:
    pttable = s3db.auth_processing_type
    query = (pttable.code == "SHARE") & \
            (pttable.deleted == False)
    row = db(query).select(pttable.id, limitby=(0, 1)).first()
    if not row:
        info("Install consent options")

        # File and Stylesheet Paths
        stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "auth", "consent_option.xsl")
        filename = os.path.join(TEMPLATE_FOLDER, "auth_consent_option.csv")

        # Import, fail on any errors
        try:
            with open(filename, "r") as File:
                resource = s3db.resource("auth_consent_option")
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
if not failed:
    info("Install CMS template for welcome messages")

    xmlstr = """
<s3xml>
    <resource name="cms_post">
    <data field="name">WelcomeMessageDisabled</data>
    <data field="body">Welcome to the {system_name} Portal!

You can edit your user profile at {profile}</data>
    <data field="comments">Rename into ”WelcomeMessage” to activate welcome message</data>
    <resource name="cms_post_module">
      <data field="module">auth</data>
      <data field="resource">user</data>
    </resource>
  </resource>
</s3xml>"""

    resource = s3db.resource("cms_post")
    try:
        tree = etree.ElementTree(etree.fromstring(xmlstr))
        resource.import_xml(tree)
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
if not failed:
    info("Upgrade GIS default config")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "gis", "config.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "gis_config.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("gis_config")
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
if not failed:
    info("Link volunteers to skills")

    query = (stable.name == "Arbeit im Gesundheitsamt") & \
            (stable.deleted == False)
    skill = db(query).select(stable.id, limitby=(0, 1)).first()
    if skill:
        skill_id = skill.id

        left = ltable.on((ltable.person_id == htable.person_id) & \
                         (ltable.skill_id == skill_id) & \
                         (ltable.deleted == False))
        query = (htable.type == 2) & \
                (htable.deleted == False) & \
                (ltable.id == None)
        rows = db(query).select(htable.person_id,
                                left = left,
                                )
        updated = 0
        for row in rows:
            data = {"person_id": row.person_id,
                    "skill_id": skill_id,
                    }
            data["id"] = ltable.insert(**data)
            auth.s3_set_record_owner(ltable, data)
            s3db.onaccept(ltable, data, method="create")
            updated += 1
        infoln("...done (%s volunteers linked)" % updated)
    else:
        infoln("...failed (Skill not found)")
        failed = True

# -----------------------------------------------------------------------------
if not failed:
    info("Update realms for all person records")

    try:
        auth.set_realm_entity(ptable, ptable.id > 0, force_update=True)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
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
