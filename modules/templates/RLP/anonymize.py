# -*- coding: utf-8 -*-

import uuid

from gluon import current

def rlp_anonymous_address(record_id, field, value):
    """
        Helper to anonymize a pr_address location; removes street and
        postcode details, but retains Lx ancestry for statistics

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the location_id
    """

    s3db = current.s3db
    db = current.db

    # Get the location
    if value:
        ltable = s3db.gis_location
        row = db(ltable.id == value).select(ltable.id,
                                            ltable.level,
                                            limitby = (0, 1),
                                            ).first()
        if not row.level:
            # Specific location => remove address details
            data = {"addr_street": None,
                    "addr_postcode": None,
                    "gis_feature_type": 0,
                    "lat": None,
                    "lon": None,
                    "wkt": None,
                    }
            # Doesn't work - PyDAL doesn't detect the None value:
            #if "the_geom" in ltable.fields:
            #    data["the_geom"] = None
            row.update_record(**data)
            if "the_geom" in ltable.fields:
                db.executesql("UPDATE gis_location SET the_geom=NULL WHERE id=%s" % row.id)

    return value

# -----------------------------------------------------------------------------
def rlp_obscure_dob(record_id, field, value):
    """
        Helper to obscure a date of birth; maps to the first day of
        the quarter, thus retaining the approximate age for statistics

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the new date
    """

    if value:
        month = int((value.month - 1) / 3) * 3 + 1
        value = value.replace(month=month, day=1)

    return value

# -----------------------------------------------------------------------------
def rlp_decline_delegation(record_id, field, value):
    """
        Decline all requested deployments when anonymizing the volunteer

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the new status
    """

    return "DECL" if value == "REQ" else value

# -----------------------------------------------------------------------------
def rlp_volunteer_anonymize():
    """ Rules to anonymize a volunteer """

    ANONYMOUS = "-"

    # Helper to produce an anonymous ID (pe_label)
    anonymous_id = lambda record_id, f, v: "NN%s" % uuid.uuid4().hex[-8:].upper()

    # Rules for delegation messages
    notifications = ("hrm_delegation_message", {"key": "delegation_id",
                                                "match": "id",
                                                "fields": {"recipient": "remove",
                                                           "subject": "remove",
                                                           "message": "remove",
                                                           },
                                                "delete": True,
                                                })

    # Rules for delegation notes
    notes = ("hrm_delegation_note", {"key": "delegation_id",
                                     "match": "id",
                                     "fields": {"note": "remove",
                                                },
                                     "delete": True,
                                     })

    rules = [# Remove identity of volunteer
             {"name": "default",
              "title": "Names, IDs, Contact Information, Addresses",
              "fields": {"first_name": ("set", ANONYMOUS),
                         "last_name": ("set", ANONYMOUS),
                         "pe_label": anonymous_id,
                         "date_of_birth": rlp_obscure_dob,
                         "comments": "remove",
                         },
              "cascade": [("pr_contact", {"key": "pe_id",
                                          "match": "pe_id",
                                          "fields": {"contact_description": "remove",
                                                     "value": ("set", ""),
                                                     "comments": "remove",
                                                     },
                                          "delete": True,
                                          }),
                          ("pr_contact_emergency", {"key": "pe_id",
                                                    "match": "pe_id",
                                                    "fields": {"name": ("set", ANONYMOUS),
                                                               "relationship": "remove",
                                                               "phone": "remove",
                                                               "comments": "remove",
                                                               },
                                                    "delete": True,
                                                    }),
                          ("pr_address", {"key": "pe_id",
                                          "match": "pe_id",
                                          "fields": {"location_id": rlp_anonymous_address,
                                                     "comments": "remove",
                                                     },
                                          }),
                          ("pr_person_details", {"key": "person_id",
                                                 "match": "id",
                                                 "fields": {"occupation": "remove",
                                                            "alias": ("set", "***"),
                                                            },
                                                 }),
                          ("hrm_human_resource", {"key": "person_id",
                                                  "match": "id",
                                                  "fields": {"status": ("set", 2),
                                                             "site_id": "remove",
                                                             "comments": "remove",
                                                             },
                                                  }),
                          ("hrm_competency", {"key": "person_id",
                                              "match": "id",
                                              "fields": {"comments": "remove",
                                                         },
                                              }),
                          ],
              },

             # Remove all free texts from delegations
             {"name": "delegations",
              "title": "Deployment Comments, Notifications and Notes",
              "cascade": [("hrm_delegation", {"key": "person_id",
                                              "match": "id",
                                              "fields": {"comments": "remove",
                                                         "status": rlp_decline_delegation,
                                                         },
                                              "cascade": [notifications,
                                                          notes,
                                                          ],
                                              }),
                          ],
              },
             ]

    return rules

# END =========================================================================
