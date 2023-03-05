import { createSlice } from "@reduxjs/toolkit";


const ProjectSlice = createSlice({
    name: 'project',
    initialState: {
        projectLoading: true,
        projectTaskBoundries: [],
        newProjectTrigger: false,
        dialogStatus: false,
        projectInfo: {},
        snackbar: {
            open: false,
            message: '',
            variant: 'info',
            duration: 0
        },
    },
    reducers: {
        SetProjectTaskBoundries(state, action) {
            state.projectTaskBoundries = action.payload
        },
        SetProjectLoading(state, action) {
            state.projectLoading = action.payload
        },
        SetDialogStatus(state, action) {
            state.dialogStatus = action.payload
        },
        SetProjectInfo(state, action) {
            state.projectInfo = action.payload
        },
        SetSnackBar(state, action) {
            state.snackbar = action.payload
        },
        SetNewProjectTrigger(state, action) {
            state.newProjectTrigger = !state.newProjectTrigger
        }
    }
})


export const ProjectActions = ProjectSlice.actions;
export default ProjectSlice;