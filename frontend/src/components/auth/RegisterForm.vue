<template>
  <v-form @submit.prevent="handleSubmit" ref="form">
    <v-text-field
        v-model="formData.email"
        :label="$t('auth.email')"
        :rules="[rules.required, rules.email]"
        type="email"
        prepend-icon="mdi-email"
    />

    <v-text-field
        v-model="formData.password"
        :label="$t('auth.password')"
        :rules="[rules.required, rules.minLength]"
        :type="showPassword ? 'text' : 'password'"
        prepend-icon="mdi-lock"
        :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
        @click:append="showPassword = !showPassword"
    />

    <v-text-field
        v-model="formData.confirmPassword"
        :label="$t('auth.confirmPassword')"
        :rules="[rules.required, rules.passwordMatch]"
        :type="showPassword ? 'text' : 'password'"
        prepend-icon="mdi-lock-check"
    />

    <v-alert v-if="error" type="error" class="mb-4">
      {{ error }}
    </v-alert>

    <v-btn
        type="submit"
        color="primary"
        block
        :loading="loading"
    >
      {{ $t('auth.registerButton') }}
    </v-btn>

    <div class="text-center mt-4">
      <router-link to="/login">
        {{ $t('auth.hasAccount') }}
      </router-link>
    </div>
  </v-form>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

const form = ref(null)
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const formData = ref({
  email: '',
  password: '',
  confirmPassword: ''
})

const rules = {
  required: value => !!value || t('validation.required'),
  email: value => /.+@.+\..+/.test(value) || t('validation.email'),
  minLength: value => (value && value.length >= 6) || t('validation.minLength', { length: 6 }),
  passwordMatch: value => value === formData.value.password || t('validation.passwordMatch')
}

const handleSubmit = async () => {
  const { valid } = await form.value.validate()
  if (!valid) return

  loading.value = true
  error.value = ''

  try {
    await authStore.register({
      email: formData.value.email,
      password: formData.value.password
    })

    router.push('/login')
  } catch (err) {
    error.value = err.response?.data?.message || t('auth.registerError')
  } finally {
    loading.value = false
  }
}
</script>