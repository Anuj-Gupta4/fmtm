<script lang="ts">
	import HotLogo from '$assets/images/hot-logo.svg';
	import HotLogoText from '$assets/images/hot-logo-text.svg';
	import Login from '$lib/components/login.svelte';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { drawerItems as menuItems } from '$constants/drawerItems.ts';
	import { revokeCookies } from '$lib/utils/login';
	import { getAlertStore } from '$store/common.svelte';
	import { getProjectSetupStepStore } from '$store/common.svelte.ts';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import type { SlDrawer, SlTooltip } from '@shoelace-style/shoelace';

	let drawerRef: SlDrawer | undefined = $state();
	let drawerOpenButtonRef: SlTooltip | undefined = $state();
	const loginStore = getLoginStore();
	const alertStore = getAlertStore();
	const projectSetupStepStore = getProjectSetupStepStore();

	let isFirstLoad = $derived(
		+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['odk_project_load'],
	);

	const handleSignOut = async () => {
		try {
			await revokeCookies();
			loginStore.signOut();
			drawerRef?.hide();
			// window.location.href = window.location.origin;
		} catch (error) {
			alertStore.setAlert({ variant: 'danger', message: 'Sign Out Failed' });
		}
	};
</script>

<div class="p-3 flex items-center justify-between font-barlow">
	<div class="flex items-center gap-1">
		<a href={window.location.origin}><img src={HotLogo} alt="hot-logo" class="h-[2.2rem] sm:h-[3rem]" /></a>
		<img src={HotLogoText} alt="hot-logo" class="h-[2.2rem] sm:h-[3rem]" />
	</div>
	<div class="flex items-center gap-4">
		<!-- profile image and username display -->
		{#if loginStore?.getAuthDetails?.username}
			<div class="flex items-center gap-2">
				{#if !loginStore?.getAuthDetails?.picture}
					<hot-icon
						name="person-fill"
						class="!text-[1.5rem] text-[#52525B] leading-0 cursor-pointer text-red-600 duration-200"
						onclick={() => {}}
						onkeydown={() => {}}
						role="button"
						tabindex="0"
					></hot-icon>
				{:else}
					<img
						src={loginStore?.getAuthDetails?.picture}
						alt="profile"
						class="w-[1.8rem] h-[1.8rem] min-w-[1.8rem] min-h-[1.8rem] max-w-[1.8rem] max-h-[1.8rem] rounded-full"
					/>
				{/if}
				<p
					class="font-medium text-sm sm:text-base text-ellipsis whitespace-nowrap overflow-hidden max-w-[6rem] sm:max-w-fit"
				>
					{loginStore?.getAuthDetails?.username}
				</p>
			</div>
		{:else}
			<sl-button
				class="hover:bg-gray-50 rounded"
				variant="text"
				size="small"
				onclick={() => {
					loginStore.toggleLoginModal(true);
				}}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') {
						loginStore.toggleLoginModal(true);
					}
				}}
				role="button"
				tabindex="0"
			>
				<span class="font-barlow font-medium text-base">SIGN IN</span>
			</sl-button>
		{/if}

		<!-- drawer component toggle trigger (snippet to reuse below) -->
		{#snippet drawerOpenButton()}
			<hot-icon
				name="list"
				class="!text-[1.8rem] text-[#52525B] leading-0 cursor-pointer hover:text-red-600 duration-200"
				style={isFirstLoad ? 'background-color: var(--sl-color-yellow-300);' : ''}
				onclick={() => {
					drawerRef?.show();
				}}
				onkeydown={() => {
					drawerRef?.show();
				}}
				role="button"
				tabindex="0"
			></hot-icon>
		{/snippet}
		<!-- add tooltip on first load -->
		{#if isFirstLoad}
			<hot-tooltip
				bind:this={drawerOpenButtonRef}
				content="First download the custom ODK Collect app here"
				open={true}
				placement="bottom"
				onsl-after-hide={() => {
					// Always keep tooltip open
					drawerOpenButtonRef?.show();
				}}
			>
				{@render drawerOpenButton()}
			</hot-tooltip>
			<!-- else render with no tooltip -->
		{:else}
			{@render drawerOpenButton()}
		{/if}
	</div>
</div>
<Login />
<hot-drawer bind:this={drawerRef} class="drawer-overview">
	<div class="flex flex-col gap-8 px-4">
		{#each menuItems as menu}
			<a
				target="_blank"
				rel="noopener noreferrer"
				href={menu.path}
				class="hover:text-red-600 cursor-pointer duration-200 decoration-none text-black font-barlow">{menu.name}</a
			>
		{/each}
		{#if loginStore?.getAuthDetails?.username}
			<sl-button
				class="primary rounded"
				variant="primary"
				size="small"
				onclick={handleSignOut}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') {
						handleSignOut();
					}
				}}
				role="button"
				tabindex="0"
			>
				<span class="font-barlow font-medium text-base">SIGN OUT</span>
			</sl-button>
		{/if}
	</div>
</hot-drawer>
