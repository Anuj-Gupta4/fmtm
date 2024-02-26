# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Logic for interaction with ODK Central & data."""

import os
from io import BytesIO
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from loguru import logger as log
from osm_fieldwork.CSVDump import CSVDump
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from pyxform.xls2xform import xls2xform_convert
from sqlalchemy.orm import Session

from app.config import settings
from app.db import db_models
from app.projects import project_schemas


def get_odk_project(odk_central: Optional[project_schemas.ODKCentralDecrypted] = None):
    """Helper function to get the OdkProject with credentials."""
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        project = OdkProject(url, user, pw)
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return project


def get_odk_form(odk_central: Optional[project_schemas.ODKCentralDecrypted] = None):
    """Helper function to get the OdkForm with credentials."""
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password

    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkForm(url, user, pw)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return form


def get_odk_app_user(odk_central: Optional[project_schemas.ODKCentralDecrypted] = None):
    """Helper function to get the OdkAppUser with credentials."""
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        log.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkAppUser(url, user, pw)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return form


def list_odk_projects(
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """List all projects on a remote ODK Server."""
    project = get_odk_project(odk_central)
    return project.listProjects()


def create_odk_project(
    name: str, odk_central: Optional[project_schemas.ODKCentralDecrypted] = None
):
    """Create a project on a remote ODK Server.

    Appends FMTM to the project name to help identify on shared servers.
    """
    project = get_odk_project(odk_central)

    try:
        log.debug(f"Attempting ODKCentral project creation: FMTM {name}")
        result = project.createProject(f"FMTM {name}")

        # Sometimes createProject returns a list if fails
        if isinstance(result, dict):
            if result.get("code") == 401.2:
                raise HTTPException(
                    status_code=500,
                    detail="Could not authenticate to odk central.",
                )

        log.debug(f"ODKCentral response: {result}")
        log.info(f"Project {name} available on the ODK Central server.")
        return result
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e


async def delete_odk_project(
    project_id: int, odk_central: Optional[project_schemas.ODKCentralDecrypted] = None
):
    """Delete a project from a remote ODK Server."""
    # FIXME: when a project is deleted from Central, we have to update the
    # odkid in the projects table
    try:
        project = get_odk_project(odk_central)
        result = project.deleteProject(project_id)
        log.info(f"Project {project_id} has been deleted from the ODK Central server.")
        return result
    except Exception:
        return "Could not delete project from central odk"


def delete_odk_app_user(
    project_id: int,
    name: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Delete an app-user from a remote ODK Server."""
    odk_app_user = get_odk_app_user(odk_central)
    result = odk_app_user.delete(project_id, name)
    return result


def upload_xform_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_credentials: Optional[dict] = None,
):
    """Upload and publish an XForm on ODKCentral."""
    title = os.path.basename(os.path.splitext(filespec)[0])

    if odk_credentials:
        url = odk_credentials["odk_central_url"]
        user = odk_credentials["odk_central_user"]
        pw = odk_credentials["odk_central_password"]

    else:
        log.debug("ODKCentral connection variables not set in function")
        log.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        xform = OdkForm(url, user, pw)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    xform.uploadMedia(project_id, title, filespec)
    result = xform.publishForm(project_id, title)
    return result


def create_odk_xform(
    odk_id: int,
    xform_path: Path,
    xform_category: str,
    feature_geojson: BytesIO,
    odk_credentials: project_schemas.ODKCentralDecrypted,
    create_draft: bool = False,
    convert_to_draft_when_publishing=True,
):
    """Create an XForm on a remote ODK Central server."""
    # result = xform.createForm(project_id, title, filespec, True)
    # Pass odk credentials of project in xform

    try:
        xform = get_odk_form(odk_credentials)
    except Exception as e:
        log.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    result = xform.createForm(odk_id, xform_path.stem, str(xform_path), create_draft)

    if result != 200 and result != 409:
        return result

    # TODO refactor osm_fieldwork.OdkCentral.OdkForm.uploadMedia
    # to accept passing a bytesio object and update
    geojson_path = Path(f"/tmp/fmtm/odk/{odk_id}/{xform_category}.geojson")
    geojson_path.parents[0].mkdir(parents=True, exist_ok=True)
    with open(geojson_path, "w") as geojson_file:
        geojson_file.write(feature_geojson.getvalue().decode("utf-8"))

    # This modifies an existing published XForm to be in draft mode.
    # An XForm must be in draft mode to upload an attachment.
    # Upload the geojson of features to be modified
    xform.uploadMedia(
        odk_id, xform_path.stem, str(geojson_path), convert_to_draft_when_publishing
    )

    # Delete temp geojson file
    geojson_path.unlink(missing_ok=True)

    result = xform.publishForm(odk_id, xform_path.stem)
    return result


def delete_odk_xform(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Delete an XForm from a remote ODK Central server."""
    xform = get_odk_form(odk_central)
    result = xform.deleteForm(project_id, xform_id)
    # FIXME: make sure it's a valid project id
    return result


def list_odk_xforms(
    project_id: int,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
    metadata: bool = False,
):
    """List all XForms in an ODK Central project."""
    project = get_odk_project(odk_central)
    xforms = project.listForms(project_id, metadata)
    # FIXME: make sure it's a valid project id
    return xforms


def get_form_full_details(
    odk_project_id: int,
    form_id: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Get additional metadata for ODK Form."""
    form = get_odk_form(odk_central)
    form_details = form.getFullDetails(odk_project_id, form_id)
    return form_details


def get_odk_project_full_details(
    odk_project_id: int, odk_central: project_schemas.ODKCentralDecrypted
):
    """Get additional metadata for ODK project."""
    project = get_odk_project(odk_central)
    project_details = project.getFullDetails(odk_project_id)
    return project_details


def list_submissions(
    project_id: int, odk_central: Optional[project_schemas.ODKCentralDecrypted] = None
):
    """List all submissions for a project, aggregated from associated users."""
    project = get_odk_project(odk_central)
    xform = get_odk_form(odk_central)
    submissions = list()
    for user in project.listAppUsers(project_id):
        for subm in xform.listSubmissions(project_id, user["displayName"]):
            submissions.append(subm)

    return submissions


def get_form_list(db: Session, skip: int, limit: int):
    """Returns the list of id and title of xforms from the database."""
    try:
        forms = (
            db.query(db_models.DbXForm.id, db_models.DbXForm.title)
            .offset(skip)
            .limit(limit)
            .all()
        )

        result_dict = []
        for form in forms:
            form_dict = {
                "id": form[0],  # Assuming the first element is the ID
                "title": form[1],  # Assuming the second element is the title
            }
            result_dict.append(form_dict)

        return result_dict

    except Exception as e:
        log.error(e)
        raise HTTPException(e) from e


def download_submissions(
    project_id: int,
    xform_id: str,
    submission_id: Optional[str] = None,
    get_json: bool = True,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Download all submissions for an XForm."""
    xform = get_odk_form(odk_central)
    # FIXME: should probably filter by timestamps or status value
    data = xform.getSubmissions(project_id, xform_id, submission_id, True, get_json)
    fixed = str(data, "utf-8")
    return fixed.splitlines()


async def test_form_validity(xform_content: str, form_type: str):
    """Validate an XForm.

    Args:
        xform_content (str): form to be tested
        form_type (str): type of form (xls or xlsx).
    """
    try:
        xlsform_path = f"/tmp/validate_form.{form_type}"
        outfile = "/tmp/outfile.xml"

        with open(xlsform_path, "wb") as f:
            f.write(xform_content)

        xls2xform_convert(xlsform_path=xlsform_path, xform_path=outfile, validate=False)

        namespaces = {
            "h": "http://www.w3.org/1999/xhtml",
            "odk": "http://www.opendatakit.org/xforms",
            "xforms": "http://www.w3.org/2002/xforms",
        }

        with open(outfile, "r") as xml:
            data = xml.read()

        root = ElementTree.fromstring(data)
        instances = root.findall(".//xforms:instance[@src]", namespaces)

        geojson_list = []
        for inst in instances:
            try:
                if "src" in inst.attrib:
                    if (inst.attrib["src"].split("."))[1] == "geojson":
                        parts = (inst.attrib["src"].split("."))[0].split("/")
                        geojson_name = parts[-1]
                        geojson_list.append(geojson_name)
            except Exception:
                continue
        return {"required media": geojson_list, "message": "Your form is valid"}
    except Exception as e:
        return JSONResponse(
            content={"message": "Your form is invalid", "possible_reason": str(e)},
            status_code=400,
        )


def generate_updated_xform(
    input_path: str,
    xform_path: Path,
    form_file_extension: str,
    form_category: str,
) -> str:
    """Update the version in an XForm so it's unique."""
    if form_file_extension != "xml":
        try:
            log.debug(f"Reading & converting xlsform -> xform: {input_path}")
            xls2xform_convert(
                xlsform_path=input_path, xform_path=str(xform_path), validate=False
            )
        except Exception as e:
            log.error(e)
            msg = f"Couldn't convert {input_path} to an XForm!"
            log.error(msg)
            raise HTTPException(status_code=400, detail=msg) from e

        if xform_path.stat().st_size <= 0:
            log.warning(f"{str(xform_path)} is empty!")
            raise HTTPException(
                status_code=400, detail=f"{str(xform_path)} is empty!"
            ) from None

        with open(xform_path, "r") as xform:
            data = xform.read()
    else:
        with open(input_path, "r") as xlsform:
            log.debug(f"Reading XForm directly: {str(input_path)}")
            data = xlsform.read()

    # # Parse the XML to geojson
    # xml = xmltodict.parse(str(data))

    # # First change the osm data extract file
    # index = 0
    # for inst in xml["h:html"]["h:head"]["model"]["instance"]:
    #     try:
    #         if "@src" in inst:
    #             if (
    #                 xml["h:html"]["h:head"]["model"]["instance"][index] \
    #                 ["@src"].split(
    #                     "."
    #                 )[1]
    #                 == "geojson"
    #             ):
    #                 xml["h:html"]["h:head"]["model"]["instance"][index][
    #                     "@src"
    #                 ] = extract

    #         if "data" in inst:
    #             print("data in inst")
    #             if "data" == inst:
    #                 print("Data = inst ", inst)
    #                 xml["h:html"]["h:head"]["model"]["instance"]["data"] \
    #                 ["@id"] = id
    #                 # xml["h:html"]["h:head"]["model"]["instance"]["data"] \
    #                 # ["@id"] = xform
    #             else:
    #                 xml["h:html"]["h:head"]["model"]["instance"][0]["data"] \
    #                 ["@id"] = id
    #     except Exception:
    #         continue
    #     index += 1
    # xml["h:html"]["h:head"]["h:title"] = name

    log.debug("Updating XML keys in XForm with data extract file & form id")
    namespaces = {
        "h": "http://www.w3.org/1999/xhtml",
        "odk": "http://www.opendatakit.org/xforms",
        "xforms": "http://www.w3.org/2002/xforms",
    }

    instances = []
    root = ElementTree.fromstring(data)
    head = root.find("h:head", namespaces)
    if head:
        model = head.find("xforms:model", namespaces)
        if model:
            instances = model.findall("xforms:instance", namespaces)

    for inst in instances:
        try:
            if "src" in inst.attrib:
                src_value = inst.attrib.get("src", "")
                if src_value.endswith(".geojson"):
                    inst.attrib["src"] = f"jr://file/{form_category}.geojson"

            # Looking for data tags
            data_tags = inst.findall("xforms:data", namespaces)
            if data_tags:
                for dt in data_tags:
                    if "id" in dt.attrib:
                        dt.attrib["id"] = str(xform_path.stem)
        except Exception as e:
            log.debug(e)
            log.warning(f"Exception parsing XForm XML: {str(xform_path)}")
            continue

    # Save the modified XML
    newxml = ElementTree.tostring(root)

    # write the updated XML file
    with open(xform_path, "wb") as outxml:
        outxml.write(newxml)

    # insert the new version
    # forms = table(
    #     "xlsforms", column("title"), column("xls"), column("xml"), column("id")
    # )
    # ins = insert(forms).values(title=name, xml=data)
    # sql = ins.on_conflict_do_update(
    #     constraint="xlsforms_title_key", set_=dict(title=name, xml=newxml)
    # )
    # db.execute(sql)
    # db.commit()

    return str(xform_path)


def upload_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Upload a data file to Central."""
    xform = get_odk_form(odk_central)
    xform.uploadMedia(project_id, xform_id, filespec)


def download_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: Optional[project_schemas.ODKCentralDecrypted] = None,
):
    """Upload a data file to Central."""
    xform = get_odk_form(odk_central)
    filename = "test"
    xform.getMedia(project_id, xform_id, filename)


def convert_csv(
    filespec: str,
    data: bytes,
):
    """Convert ODK CSV to OSM XML and GeoJson."""
    csvin = CSVDump("/xforms.yaml")

    osmoutfile = f"{filespec}.osm"
    csvin.createOSM(osmoutfile)

    jsonoutfile = f"{filespec}.geojson"
    csvin.createGeoJson(jsonoutfile)

    if len(data) == 0:
        log.debug("Parsing csv file %r" % filespec)
        # The yaml file is in the package files for osm_fieldwork
        data = csvin.parse(filespec)
    else:
        csvdata = csvin.parse(filespec, data)
        for entry in csvdata:
            log.debug(f"Parsing csv data {entry}")
            if len(data) <= 1:
                continue
            feature = csvin.createEntry(entry)
            # Sometimes bad entries, usually from debugging XForm design, sneak in
            if len(feature) > 0:
                if "tags" not in feature:
                    log.warning("Bad record! %r" % feature)
                else:
                    if "lat" not in feature["attrs"]:
                        import epdb

                        epdb.st()
                    csvin.writeOSM(feature)
                    # This GeoJson file has all the data values
                    csvin.writeGeoJson(feature)
                    pass

    csvin.finishOSM()
    csvin.finishGeoJson()

    return True
