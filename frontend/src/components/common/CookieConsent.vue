<template>
  <v-snackbar
      v-model="showConsent"
      :timeout="-1"
      location="bottom"
      class="cookie-consent"
      color="background"
      elevation="4"
  >
    <div class="d-flex flex-column flex-sm-row align-center">
      <div class="text-body-1 mr-4">
        {{ $t('cookies.message') }}
        <v-btn
            variant="text"
            color="primary"
            size="small"
            class="ml-1 px-1"
            @click="showPrivacyDialog = true"
        >
          {{ $t('cookies.learnMore') }}
        </v-btn>
      </div>
      <v-spacer></v-spacer>
      <div class="d-flex mt-2 mt-sm-0">
        <v-btn
            color="primary"
            variant="flat"
            @click="acceptCookies"
            class="ml-2"
        >
          {{ $t('cookies.accept') }}
        </v-btn>
        <v-btn
            color="grey-darken-1"
            variant="outlined"
            @click="declineCookies"
            class="ml-2"
        >
          {{ $t('cookies.decline') }}
        </v-btn>
      </div>
    </div>
  </v-snackbar>

  <!-- Privacy Policy Dialog -->
  <v-dialog v-model="showPrivacyDialog" max-width="800">
    <v-card>
      <v-card-title class="text-h5">
        {{ $t('cookies.privacyTitle') }}
      </v-card-title>
      <v-card-text>
        <p class="text-body-1 mb-4">{{ $t('cookies.privacyIntro') }}</p>

        <h3 class="text-h6 mb-2">{{ $t('cookies.whatAreCookies') }}</h3>
        <p class="text-body-2 mb-4">{{ $t('cookies.cookiesExplanation') }}</p>

        <h3 class="text-h6 mb-2">{{ $t('cookies.typesTitle') }}</h3>
        <p class="text-body-2">{{ $t('cookies.essentialTitle') }}</p>
        <p class="text-body-2 mb-2">{{ $t('cookies.essentialDescription') }}</p>

        <p class="text-body-2">{{ $t('cookies.preferencesTitle') }}</p>
        <p class="text-body-2 mb-2">{{ $t('cookies.preferencesDescription') }}</p>

        <p class="text-body-2">{{ $t('cookies.statisticsTitle') }}</p>
        <p class="text-body-2 mb-2">{{ $t('cookies.statisticsDescription') }}</p>

        <h3 class="text-h6 mb-2 mt-4">{{ $t('cookies.managingTitle') }}</h3>
        <p class="text-body-2 mb-4">{{ $t('cookies.managingDescription') }}</p>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="showPrivacyDialog = false">
          {{ $t('common.close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const showConsent = ref(false);
const showPrivacyDialog = ref(false);

// Cookie consent storage key
const COOKIE_CONSENT_KEY = 'cookie-consent-accepted';

// Check if user has already accepted cookies
const checkCookieConsent = () => {
  const consentStatus = localStorage.getItem(COOKIE_CONSENT_KEY);
  return consentStatus === 'true';
};

// Accept cookies
const acceptCookies = () => {
  localStorage.setItem(COOKIE_CONSENT_KEY, 'true');
  showConsent.value = false;
};

// Decline cookies
const declineCookies = () => {
  localStorage.setItem(COOKIE_CONSENT_KEY, 'false');
  showConsent.value = false;

  // Here you might want to disable any non-essential cookies or tracking
  // For example, you could emit an event that other components can listen for
};

// On component mount, check if we need to show the consent dialog
onMounted(() => {
  // Only show if consent hasn't been given yet
  if (!checkCookieConsent()) {
    showConsent.value = true;
  }
});
</script>

<style scoped>
.cookie-consent {
  max-width: 100% !important;
}
</style>