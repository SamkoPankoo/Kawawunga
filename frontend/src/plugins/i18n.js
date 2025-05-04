import { createI18n } from 'vue-i18n'
import sk from '../locales/sk.json'
import en from '../locales/en.json'

const i18n = createI18n({
    legacy: false,
    locale: localStorage.getItem('language') || 'sk',
    fallbackLocale: 'en',
    messages: {
        sk,
        en
    }
})

export default i18n