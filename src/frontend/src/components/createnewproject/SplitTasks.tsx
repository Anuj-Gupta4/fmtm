import React, { useEffect, useState } from 'react';
import Button from '@/components/common/Button';
import RadioButton from '@/components/common/RadioButton';
import AssetModules from '@/shared/AssetModules.js';
import { CommonActions } from '@/store/slices/CommonSlice';
import { useNavigate } from 'react-router-dom';
import { CreateProjectActions } from '@/store/slices/CreateProjectSlice';
import useForm from '@/hooks/useForm';
import DefineTaskValidation from '@/components/createnewproject/validation/DefineTaskValidation';
import NewDefineAreaMap from '@/views/NewDefineAreaMap';
import { useAppDispatch, useAppSelector } from '@/types/reduxTypes';
import {
  CreateProjectService,
  GetDividedTaskFromGeojson,
  TaskSplittingPreviewService,
} from '@/api/CreateProjectService';
import { task_split_type } from '@/types/enums';
import useDocumentTitle from '@/utilfunctions/useDocumentTitle';
import { taskSplitOptionsType } from '@/store/types/ICreateProject';
import DescriptionSection from '@/components/createnewproject/Description';

const SplitTasks = ({ flag, setGeojsonFile, customDataExtractUpload, additionalFeature, customFormFile }) => {
  useDocumentTitle('Create Project: Split Tasks');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const [taskGenerationStatus, setTaskGenerationStatus] = useState(false);

  const splitTasksSelection = useAppSelector((state) => state.createproject.splitTasksSelection);
  const drawnGeojson = useAppSelector((state) => state.createproject.drawnGeojson);
  const projectDetails = useAppSelector((state) => state.createproject.projectDetails);
  const dataExtractGeojson = useAppSelector((state) => state.createproject.dataExtractGeojson);

  const generateProjectSuccess = useAppSelector((state) => state.createproject.generateProjectSuccess);
  const generateProjectError = useAppSelector((state) => state.createproject.generateProjectError);
  const projectDetailsResponse = useAppSelector((state) => state.createproject.projectDetailsResponse);
  const dividedTaskGeojson = useAppSelector((state) => state.createproject.dividedTaskGeojson);
  const projectDetailsLoading = useAppSelector((state) => state.createproject.projectDetailsLoading);
  const dividedTaskLoading = useAppSelector((state) => state.createproject.dividedTaskLoading);
  const taskSplittingGeojsonLoading = useAppSelector((state) => state.createproject.taskSplittingGeojsonLoading);
  const isTasksGenerated = useAppSelector((state) => state.createproject.isTasksGenerated);
  const isFgbFetching = useAppSelector((state) => state.createproject.isFgbFetching);
  const toggleSplittedGeojsonEdit = useAppSelector((state) => state.createproject.toggleSplittedGeojsonEdit);
  const additionalFeatureGeojson = useAppSelector((state) => state.createproject.additionalFeatureGeojson);

  const taskSplitOptions: taskSplitOptionsType[] = [
    {
      name: 'define_tasks',
      value: task_split_type.DIVIDE_ON_SQUARE,
      label: 'Divide into square tasks',
      disabled: false,
    },
    {
      name: 'define_tasks',
      value: task_split_type.CHOOSE_AREA_AS_TASK,
      label: 'Use uploaded AOI as task areas',
      disabled: false,
    },
    {
      name: 'define_tasks',
      value: task_split_type.TASK_SPLITTING_ALGORITHM,
      label: 'Task Splitting Algorithm',
      disabled: false,
    },
  ];

  const toggleStep = (step: number, url: string) => {
    dispatch(CommonActions.SetCurrentStepFormStep({ flag: flag, step: step }));
    navigate(url);
    dispatch(CreateProjectActions.SetToggleSplittedGeojsonEdit(false));
  };

  const checkTasksGeneration = () => {
    if (!isTasksGenerated.divide_on_square && splitTasksSelection === task_split_type.DIVIDE_ON_SQUARE) {
      setTaskGenerationStatus(false);
    } else if (
      !isTasksGenerated.task_splitting_algorithm &&
      splitTasksSelection === task_split_type.TASK_SPLITTING_ALGORITHM
    ) {
      setTaskGenerationStatus(false);
    } else {
      setTaskGenerationStatus(true);
    }
  };

  useEffect(() => {
    checkTasksGeneration();
  }, [splitTasksSelection, isTasksGenerated]);

  const submission = () => {
    dispatch(CreateProjectActions.SetIsUnsavedChanges(false));

    dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
    // Project POST data
    let projectData = {
      name: projectDetails.name,
      short_description: projectDetails.short_description,
      description: projectDetails.description,
      per_task_instructions: projectDetails.per_task_instructions,
      // Use split task areas, or project area if no task splitting
      outline: drawnGeojson,
      odk_central_url: projectDetails.odk_central_url,
      odk_central_user: projectDetails.odk_central_user,
      odk_central_password: projectDetails.odk_central_password,
      // dont send xform_category if upload custom form is selected
      xform_category: projectDetails.formCategorySelection,
      task_split_type: splitTasksSelection,
      form_ways: projectDetails.formWays,
      // "uploaded_form": projectDetails.uploaded_form,
      hashtags: projectDetails.hashtags,
      data_extract_url: projectDetails.data_extract_url,
      custom_tms_url: projectDetails.custom_tms_url,
    };
    // Append extra param depending on task split type
    if (splitTasksSelection === task_split_type.TASK_SPLITTING_ALGORITHM) {
      projectData = { ...projectData, task_num_buildings: projectDetails.average_buildings_per_task };
    } else {
      projectData = { ...projectData, task_split_dimension: projectDetails.dimension };
    }
    // Create file object from generated task areas
    const taskAreaBlob = new Blob([JSON.stringify(dividedTaskGeojson || drawnGeojson)], {
      type: 'application/json',
    });
    // Create a file object from the Blob
    const taskAreaGeojsonFile = new File([taskAreaBlob], 'data.json', { type: 'application/json' });

    // FIXME for now hardcoded as Polygon projects (add project creation UI for user selection)
    // projectData = { ...projectData, new_geom_type: projectDetails.new_geom_type };
    projectData = { ...projectData, new_geom_type: 'POLYGON' };

    dispatch(
      CreateProjectService(
        `${import.meta.env.VITE_API_URL}/projects?org_id=${projectDetails.organisation_id}`,
        projectData,
        taskAreaGeojsonFile,
        customFormFile,
        customDataExtractUpload,
        projectDetails.dataExtractWays === 'osm_data_extract',
        additionalFeature,
        projectDetails.project_admins as number[],
      ),
    );
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, ...formValues }));
    dispatch(CreateProjectActions.SetCanSwitchCreateProjectSteps(true));
  };

  useEffect(() => {
    if (splitTasksSelection === task_split_type.CHOOSE_AREA_AS_TASK) {
      dispatch(CreateProjectActions.SetDividedTaskGeojson(null));
    }
  }, [splitTasksSelection]);

  const {
    handleSubmit,
    handleCustomChange,
    values: formValues,
    errors,
  }: any = useForm(projectDetails, submission, DefineTaskValidation);

  const generateTaskBasedOnSelection = (e) => {
    dispatch(CreateProjectActions.SetIndividualProjectDetailsData({ ...projectDetails, ...formValues }));

    e.preventDefault();
    e.stopPropagation();
    // Create a file object from the project area Blob
    const projectAreaBlob = new Blob([JSON.stringify(drawnGeojson)], { type: 'application/json' });
    const drawnGeojsonFile = new File([projectAreaBlob], 'outline.json', { type: 'application/json' });

    // Create a file object from the data extract Blob
    const dataExtractBlob = new Blob([JSON.stringify(dataExtractGeojson)], { type: 'application/json' });
    const dataExtractFile = new File([dataExtractBlob], 'extract.json', { type: 'application/json' });

    if (splitTasksSelection === task_split_type.DIVIDE_ON_SQUARE) {
      dispatch(
        GetDividedTaskFromGeojson(`${import.meta.env.VITE_API_URL}/projects/preview-split-by-square`, {
          geojson: drawnGeojsonFile,
          extract_geojson: formValues.dataExtractWays === 'osm_data_extract' ? null : dataExtractFile,
          dimension: formValues?.dimension,
        }),
      );
    } else if (splitTasksSelection === task_split_type.TASK_SPLITTING_ALGORITHM) {
      dispatch(
        TaskSplittingPreviewService(
          `${import.meta.env.VITE_API_URL}/projects/task-split`,
          drawnGeojsonFile,
          formValues?.average_buildings_per_task,
          // Only send dataExtractFile if custom extract
          formValues.dataExtractWays === 'osm_data_extract' ? null : dataExtractFile,
        ),
      );
    }
  };

  useEffect(() => {
    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    const handleQRGeneration = async () => {
      if (!generateProjectError && generateProjectSuccess) {
        const projectId = projectDetailsResponse?.id;
        dispatch(
          CommonActions.SetSnackBar({
            open: true,
            message: 'Project Generation Completed. Redirecting...',
            variant: 'success',
            duration: 2000,
          }),
        );

        // Add 5-second delay to allow backend Entity generation to catch up
        await delay(5000);
        dispatch(CreateProjectActions.CreateProjectLoading(false));
        navigate(`/project/${projectId}`);
        dispatch(CreateProjectActions.ClearCreateProjectFormData());
        dispatch(CreateProjectActions.SetCanSwitchCreateProjectSteps(false));
      }
    };

    handleQRGeneration();
  }, [generateProjectSuccess, generateProjectError]);

  const renderTraceback = (errorText: string) => {
    if (!errorText) {
      return null;
    }

    return errorText.split('\n').map((line, index) => (
      <div key={index} style={{ display: 'flex' }}>
        <span style={{ color: 'gray', marginRight: '1em' }}>{index + 1}.</span>
        <span>{line}</span>
      </div>
    ));
  };

  const parsedTaskGeojsonCount = dividedTaskGeojson?.features?.length || drawnGeojson?.features?.length || 1;
  const totalSteps = dividedTaskGeojson?.features ? dividedTaskGeojson?.features?.length : parsedTaskGeojsonCount;
  return (
    <>
      <form onSubmit={handleSubmit} className="fmtm-h-full">
        <div className="fmtm-flex fmtm-gap-7 fmtm-flex-col lg:fmtm-flex-row fmtm-h-full">
          <DescriptionSection section="Split Tasks" />
          <div className="lg:fmtm-w-[80%] xl:fmtm-w-[83%] fmtm-bg-white fmtm-px-5 lg:fmtm-px-11 fmtm-py-6 lg:fmtm-overflow-y-scroll lg:scrollbar">
            <div className="fmtm-w-full fmtm-flex fmtm-gap-6 md:fmtm-gap-14 fmtm-flex-col md:fmtm-flex-row fmtm-h-full">
              <div className="fmtm-flex fmtm-flex-col fmtm-gap-6 lg:fmtm-w-[40%] fmtm-justify-between">
                <div>
                  <RadioButton
                    value={splitTasksSelection || ''}
                    topic="Select an option to split your project area"
                    options={taskSplitOptions}
                    direction="column"
                    onChangeData={(value) => {
                      handleCustomChange('task_split_type', value);
                      dispatch(CreateProjectActions.SetSplitTasksSelection(value as task_split_type));
                      if (task_split_type.CHOOSE_AREA_AS_TASK === value) {
                        dispatch(CreateProjectActions.SetIsTasksGenerated({ key: 'divide_on_square', value: false }));
                        dispatch(
                          CreateProjectActions.SetIsTasksGenerated({ key: 'task_splitting_algorithm', value: false }),
                        );
                      }
                    }}
                    errorMsg={errors.task_split_type}
                    hoveredOption={(hoveredOption) =>
                      dispatch(
                        CreateProjectActions.SetDescriptionToFocus(
                          hoveredOption ? `splittasks-${hoveredOption}` : null,
                        ),
                      )
                    }
                  />
                  <div className="fmtm-mt-5">
                    <p className="fmtm-text-gray-500">
                      Total number of features:{' '}
                      <span className="fmtm-font-bold">{dataExtractGeojson?.features?.length || 0}</span>
                    </p>
                  </div>
                  {splitTasksSelection === task_split_type.DIVIDE_ON_SQUARE && (
                    <>
                      <div className="fmtm-mt-6 fmtm-flex fmtm-items-center fmtm-gap-4">
                        <p className="fmtm-text-gray-500">Dimension of square in metres: </p>
                        <input
                          type="number"
                          value={formValues.dimension}
                          onChange={(e) => handleCustomChange('dimension', e.target.value)}
                          className="fmtm-outline-none fmtm-border-[1px] fmtm-border-gray-600 fmtm-h-7 fmtm-w-16 fmtm-px-2 "
                        />
                      </div>
                      {errors.dimension && (
                        <div>
                          <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">{errors.dimension}</p>
                        </div>
                      )}
                    </>
                  )}
                  {splitTasksSelection === task_split_type.TASK_SPLITTING_ALGORITHM && (
                    <>
                      <div className="fmtm-mt-6 fmtm-flex fmtm-items-center fmtm-gap-4">
                        <p className="fmtm-text-gray-500">Average number of buildings per task: </p>
                        <input
                          type="number"
                          value={formValues.average_buildings_per_task}
                          onChange={(e) => handleCustomChange('average_buildings_per_task', parseInt(e.target.value))}
                          className="fmtm-outline-none fmtm-border-[1px] fmtm-border-gray-600 fmtm-h-7 fmtm-w-16 fmtm-px-2 "
                        />
                      </div>
                      {errors.average_buildings_per_task && (
                        <div>
                          <p className="fmtm-form-error fmtm-text-red-600 fmtm-text-sm fmtm-py-1">
                            {errors.average_buildings_per_task}
                          </p>
                        </div>
                      )}
                    </>
                  )}
                  {(splitTasksSelection === task_split_type.DIVIDE_ON_SQUARE ||
                    splitTasksSelection === task_split_type.TASK_SPLITTING_ALGORITHM) && (
                    <div className="fmtm-mt-6 fmtm-pb-3">
                      <div className="fmtm-flex fmtm-items-center fmtm-gap-4">
                        <Button
                          btnText="Click to generate task"
                          btnType="primary"
                          type="button"
                          isLoading={dividedTaskLoading || taskSplittingGeojsonLoading}
                          onClick={generateTaskBasedOnSelection}
                          className=""
                          icon={<AssetModules.SettingsIcon className="fmtm-text-white" />}
                          disabled={
                            (splitTasksSelection === task_split_type.TASK_SPLITTING_ALGORITHM &&
                              !formValues?.average_buildings_per_task) ||
                            isFgbFetching
                              ? true
                              : false
                          }
                        />
                      </div>
                    </div>
                  )}
                  {(splitTasksSelection === task_split_type.DIVIDE_ON_SQUARE ||
                    splitTasksSelection === task_split_type.TASK_SPLITTING_ALGORITHM ||
                    splitTasksSelection === task_split_type.CHOOSE_AREA_AS_TASK) && (
                    <div>
                      <p className="fmtm-text-gray-500 fmtm-mt-5">
                        Total number of task: <span className="fmtm-font-bold">{totalSteps}</span>
                      </p>
                    </div>
                  )}
                </div>
                <div className="fmtm-flex fmtm-gap-5 fmtm-mx-auto fmtm-mt-10 fmtm-my-5">
                  <Button
                    btnText="PREVIOUS"
                    btnType="secondary"
                    type="button"
                    onClick={() => {
                      dispatch(CreateProjectActions.SetIndividualProjectDetailsData(formValues));
                      toggleStep(3, '/map-data');
                    }}
                    className="fmtm-font-bold"
                  />
                  <Button
                    isLoading={projectDetailsLoading}
                    btnText="SUBMIT"
                    btnType="primary"
                    type="submit"
                    className="fmtm-font-bold"
                    disabled={taskGenerationStatus ? false : true}
                  />
                </div>
              </div>
              <div className="fmtm-w-full lg:fmtm-w-[60%] fmtm-flex fmtm-flex-col fmtm-gap-6 fmtm-bg-gray-300 fmtm-h-[60vh] lg:fmtm-h-full">
                <NewDefineAreaMap
                  splittedGeojson={dividedTaskGeojson}
                  uploadedOrDrawnGeojsonFile={drawnGeojson}
                  buildingExtractedGeojson={dataExtractGeojson}
                  onModify={
                    toggleSplittedGeojsonEdit
                      ? (geojson) => {
                          handleCustomChange('drawnGeojson', geojson);
                          dispatch(CreateProjectActions.SetDividedTaskGeojson(JSON.parse(geojson)));
                          setGeojsonFile(null);
                        }
                      : null
                  }
                  // toggleSplittedGeojsonEdit
                  hasEditUndo
                  additionalFeatureGeojson={additionalFeatureGeojson}
                />
              </div>
            </div>
          </div>
        </div>
      </form>
    </>
  );
};

export default SplitTasks;
