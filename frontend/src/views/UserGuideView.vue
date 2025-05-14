<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <div class="text-h4">{{ $t('userGuide.title') }}</div>
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                prepend-icon="mdi-file-pdf-box"
                @click="downloadPdf"
                :loading="loading"
            >
              {{ $t('userGuide.downloadPdf') }}
            </v-btn>
          </v-card-title>
        </v-card>
      </v-col>
    </v-row>

    <div id="user-guide-content">
      <v-row>
        <!-- Navigácia -->
        <v-col cols="12" md="3">
          <v-card>
            <v-list nav>
              <v-list-item
                  v-for="section in sections"
                  :key="section.id"
                  :value="section.id"
                  :href="'#' + section.id"
                  @click.prevent="scrollToSection(section.id)"
              >
                <v-list-item-title>{{ $t(section.title) }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>

        <!-- Obsah -->
        <v-col cols="12" md="9">
          <v-card>
            <v-card-text>
              <!-- Úvod -->
              <section :id="sections[0].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.introduction') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.introText') }}</p>
                <p class="text-body-1">
                  PDF Editor umožňuje používateľom jednoducho manipulovať s PDF súbormi priamo vo webovom prehliadači.
                  Nepotrebujete inštalovať žiadny dodatočný softvér - stačí sa prihlásiť a začať pracovať s vašimi PDF dokumentmi.
                </p>
                <v-img
                    src="@/assets/intro-image.png"
                    alt="PDF Editor Interface"
                    class="my-4"
                    contain
                    max-height="300"
                ></v-img>
              </section>

              <!-- Začíname -->
              <section :id="sections[1].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.gettingStarted') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.gettingStartedText') }}</p>

                <h3 class="text-h5 mt-4 mb-2">Registrácia</h3>
                <ol class="text-body-1">
                  <li>Kliknite na tlačidlo "Registrácia" v hornom menu</li>
                  <li>Vyplňte svoju emailovú adresu a heslo</li>
                  <li>Kliknite na tlačidlo "Registrovať sa"</li>
                </ol>

                <h3 class="text-h5 mt-4 mb-2">Prihlásenie</h3>
                <ol class="text-body-1">
                  <li>Kliknite na tlačidlo "Prihlásenie" v hornom menu</li>
                  <li>Zadajte svoju emailovú adresu a heslo</li>
                  <li>Kliknite na tlačidlo "Prihlásiť sa"</li>
                </ol>

                <h3 class="text-h5 mt-4 mb-2">Dashboard</h3>
                <p class="text-body-1">
                  Po prihlásení sa zobrazí dashboard, kde uvidíte:
                </p>
                <ul class="text-body-1">
                  <li>Nedávnu aktivitu - zoznam naposledy upravených súborov</li>
                  <li>Rýchly prístup - skratky k najpoužívanejším nástrojom</li>
                  <li>API prístup - váš API kľúč pre programový prístup k službám</li>
                </ul>
              </section>

              <!-- Funkcie a nástroje -->
              <section :id="sections[2].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.features') }}</h2>
                <p class="text-body-1">
                  PDF Editor poskytuje nasledujúce funkcie pre prácu s PDF súbormi:
                </p>

                <div v-for="(feature, index) in features" :key="index" class="mb-6">
                  <h3 class="text-h5 mb-2">{{ $t(feature.title) }}</h3>
                  <p class="text-body-1">{{ $t(feature.description) }}</p>
                  <v-card variant="outlined" class="pa-4 my-2">
                    <h4 class="text-subtitle-1 font-weight-bold">Použitie:</h4>
                    <div class="pl-1">
                      <ol class="text-body-1 pl-4">
                        <li v-for="(step, i) in feature.steps" :key="i">
                          {{ step }}
                        </li>
                      </ol>
                    </div>
                  </v-card>
                </div>
              </section>

              <!-- API -->
              <section :id="sections[3].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.apiUsage') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.apiUsageText') }}</p>

                <h3 class="text-h5 mt-4 mb-2">Získanie API kľúča</h3>
                <p class="text-body-1">
                  Váš osobný API kľúč nájdete na dashboarde v sekcii "API Prístup". Tento kľúč musíte zahrnúť v hlavičke každého API požiadavku.
                </p>

                <h3 class="text-h5 mt-4 mb-2">Autentifikácia</h3>
                <v-card variant="outlined" class="pa-4 my-2 bg-grey-lighten-4">
                  <pre class="language-bash"><code>curl -X POST https://api.pdfeditor.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "vas@email.com", "password": "vase_heslo"}'</code></pre>
                </v-card>

                <h3 class="text-h5 mt-4 mb-2">Používanie API</h3>
                <p class="text-body-1">
                  Pri každom API požiadavku musíte pridať hlavičku s vaším API kľúčom:
                </p>
                <v-card variant="outlined" class="pa-4 my-2 bg-grey-lighten-4">
                  <pre class="language-bash"><code>curl -X POST https://api.pdfeditor.com/api/merge \
  -H "X-API-Key: vas_api_kluc" \
  -F "file1=@cesta/k/suboru1.pdf" \
  -F "file2=@cesta/k/suboru2.pdf"</code></pre>
                </v-card>

                <p class="text-body-1 mt-4">
                  Úplnú dokumentáciu API nájdete v sekcii "API Dokumentácia" v hlavnom menu.
                </p>
              </section>

              <!-- Časté problémy -->
              <section :id="sections[4].id" class="guide-section">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.commonIssues') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.commonIssuesText') }}</p>

                <v-expansion-panels class="mt-4">
                  <v-expansion-panel
                      v-for="(issue, index) in commonIssues"
                      :key="index"
                  >
                    <v-expansion-panel-title>
                      {{ issue.question }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <p class="text-body-1">{{ issue.answer }}</p>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </section>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup>
import { ref, onMounted, getCurrentInstance } from 'vue';
import axios from 'axios';

const loading = ref(false);

const sections = [
  { id: 'introduction', title: 'userGuide.introduction' },
  { id: 'getting-started', title: 'userGuide.gettingStarted' },
  { id: 'features', title: 'userGuide.features' },
  { id: 'api-usage', title: 'userGuide.apiUsage' },
  { id: 'common-issues', title: 'userGuide.commonIssues' }
];

const features = [
  {
    title: 'pdf.mergePdf',
    description: 'pdf.mergePdfDesc',
    steps: [
      'Prejdite na stránku "Zlúčiť PDF"',
      'Nahratie PDF súborov, ktoré chcete zlúčiť',
      'Usporiadajte súbory do požadovaného poradia presunom nahor/nadol',
      'Kliknite na tlačidlo "Zlúčiť"',
      'Po dokončení stiahnite zlúčený PDF súbor'
    ]
  },
  {
    title: 'pdf.splitPdf',
    description: 'pdf.splitPdfDesc',
    steps: [
      'Prejdite na stránku "Rozdeliť PDF"',
      'Nahrajte PDF súbor, ktorý chcete rozdeliť',
      'Vyberte metódu rozdelenia (po stranách, podľa rozsahu, extrakcia konkrétnych strán)',
      'Zadajte požadované strany alebo rozsahy',
      'Kliknite na tlačidlo "Rozdeliť"',
      'Po dokončení stiahnite výsledné PDF súbory alebo ZIP archív'
    ]
  },
  {
    title: 'pdf.watermarkPdf',
    description: 'pdf.watermarkPdfDesc',
    steps: [
      'Prejdite na stránku "Pridať vodoznak"',
      'Nahrajte PDF súbor, do ktorého chcete pridať vodoznak',
      'Zadajte text vodoznaku',
      'Upravte parametre vodoznaku (priehľadnosť, veľkosť, farba, uhol)',
      'Vyberte strany, na ktoré sa má vodoznak aplikovať',
      'Kliknite na tlačidlo "Aplikovať vodoznak"',
      'Po dokončení stiahnite výsledný PDF súbor'
    ]
  },
  {
    title: 'pdf.rotatePdf',
    description: 'pdf.rotatePdfDesc',
    steps: [
      'Prejdite na stránku "Otočiť PDF"',
      'Nahrajte PDF súbor, ktorý chcete otočiť',
      'Vyberte uhol otočenia (90°, 180°, 270°)',
      'Vyberte strany, ktoré chcete otočiť',
      'Kliknite na tlačidlo "Otočiť"',
      'Po dokončení stiahnite výsledný PDF súbor'
    ]
  },
  {
    title: 'pdf.deletePages',
    description: 'pdf.deletePagesDesc',
    steps: [
      'Prejdite na stránku "Vymazať stránky"',
      'Nahrajte PDF súbor, z ktorého chcete vymazať stránky',
      'Vyberte strany, ktoré chcete vymazať',
      'Kliknite na tlačidlo "Vymazať stránky"',
      'Po dokončení stiahnite výsledný PDF súbor'
    ]
  }
];

const commonIssues = [
  {
    question: 'Nedokážem nahrať súbor väčší ako 50 MB',
    answer: 'PDF Editor má momentálne limit 50 MB pre nahrávané súbory. Ak potrebujete spracovať väčšie súbory, skúste ich najprv rozdeliť na menšie časti alebo použiť nástroj na kompresiu PDF.'
  },
  {
    question: 'Ako môžem zlúčiť viac ako 10 PDF súborov?',
    answer: 'Aj keď rozhranie zobrazuje možnosť nahrať maximálne 10 súborov naraz, môžete zlúčiť viac súborov postupne. Najprv zlúčte prvých 10 súborov, potom použite výsledný súbor a zlúčte ho s ďalšími súbormi.'
  },
  {
    question: 'Moje heslo chránené PDF sa nedá spracovať',
    answer: 'PDF Editor momentálne nepodporuje spracovanie heslo chránených PDF súborov. Pred nahratím do aplikácie musíte odstrániť heslo z PDF (pomocou pôvodnej aplikácie, v ktorej bol PDF vytvorený).'
  },
  {
    question: 'Po zlúčení PDF sa stratilo formátovanie/fonty',
    answer: 'Niektoré PDF súbory používajú špeciálne fonty, ktoré nemusia byť správne vložené do dokumentu. Odporúčame, aby ste si výsledný PDF súbor vždy skontrolovali a v prípade problémov s formátovaním skúste pôvodné súbory uložiť s vloženými fontami.'
  },
  {
    question: 'Ako môžem vytvoriť nový API kľúč?',
    answer: 'Nový API kľúč môžete vygenerovať na Dashboarde v sekcii "API Prístup". Kliknite na tlačidlo "Vygenerovať nový kľúč". Upozorňujeme, že po vygenerovaní nového kľúča bude predchádzajúci kľúč neplatný.'
  }
];

const scrollToSection = (sectionId) => {
  const element = document.getElementById(sectionId);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
  }
};

const downloadPdf = async () => {
  loading.value = true;

  try {
    // Dynamické načítanie html2pdf.js
    // Toto riešenie používa dynamický import na načítanie knižnice len vtedy, keď je potrebná
    await new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
    const html2pdf = window.html2pdf;


    // Získanie obsahu príručky
    const content = document.getElementById('user-guide-content');

    // Odstránenie nepotrebných elementov pre PDF export
    const clonedContent = content.cloneNode(true);
    const buttonElements = clonedContent.querySelectorAll('button, .v-btn');
    buttonElements.forEach(el => el.parentNode.removeChild(el));

    // Konfigurácia PDF
    const options = {
      margin: 10,
      filename: 'pdfeditor-user-guide.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // Generovanie PDF
    // Použitie metódy from().set().save() namiesto priameho volania save()
    await html2pdf()
        .from(clonedContent)
        .set(options)
        .save();

    // Pre logovanie tejto operácie do histórie
    try {
      // Get auth store
      const authStore = useAuthStore();

      // Make sure we have auth credentials
      if (authStore.isAuthenticated) {
        // Prepare headers with both token and API key (if available)
        const headers = {};

        if (authStore.token) {
          headers['Authorization'] = `Bearer ${authStore.token}`;
        }

        if (authStore.user?.apiKey) {
          headers['X-API-Key'] = authStore.user.apiKey;
        }

        // Only log if we have authentication
        if (Object.keys(headers).length > 0) {
          await axios.post(
              `${import.meta.env.VITE_API_URL}/history/log`,
              {
                action: 'export-user-guide',
                description: 'Exported user guide to PDF',
                metadata: {
                  operationType: 'export',
                  timestamp: new Date().toISOString()
                }
              },
              { headers }
          );
        }
      }
    } catch (logError) {
      console.warn('Failed to log PDF export operation:', logError);
    }
  } catch (error) {
    console.error('Error generating PDF:', error);
    alert('Nastala chyba pri generovaní PDF. Prosím, skúste to znovu neskôr.');
  } finally {
    loading.value = false;
  }
};

</script>

<style scoped>
.guide-section {
  scroll-margin-top: 70px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
}

/* Oprava paddingu pro seznam uvnitř rámečků */
v-card.pa-4 ol {
  padding-left: 10rem !important;
}


/* Obecná úprava všech seznamů v dokumentu */
.text-body-1 ol,
.text-body-1 ul {
  padding-left: 2rem;
}

/* Zajištění responzivity seznamů na menších obrazovkách */
@media (max-width: 600px) {
  v-card.pa-4 ol,
  .text-body-1 ol,
  .text-body-1 ul {
    padding-left: 1.5rem;
  }
}
</style>