<template>
  <div class="min-h-screen overflow-hidden bg-white text-slate-900">
    <header class="border-b border-slate-100 bg-white/90">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <RouterLink to="/" class="flex items-center gap-3 no-underline">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-xl shadow-sm">
            🇩🇪
          </span>
          <span class="text-lg font-bold tracking-tight text-slate-900">
            German Exercises
          </span>
        </RouterLink>

        <RouterLink
          to="/login"
          class="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
        >
          Anmelden
        </RouterLink>
      </div>
    </header>

    <main>
      <section class="relative isolate overflow-hidden border-b border-slate-100 bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div class="pointer-events-none absolute -right-24 -top-24 -z-10 h-80 w-80 rounded-full bg-blue-200/30 blur-3xl"></div>

        <div class="mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-2 lg:gap-16 lg:px-8 lg:py-24">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-white/80 px-3 py-1.5 text-sm font-medium text-blue-700 shadow-sm">
              <span class="h-2 w-2 rounded-full bg-blue-600"></span>
              Ihr Lernraum für Deutsch
            </div>

            <h1 class="mt-6 max-w-2xl text-4xl font-bold leading-tight tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
              Deutsch lernen.
              <span class="text-blue-600">Schritt für Schritt.</span>
            </h1>

            <p class="mt-6 max-w-xl text-lg leading-8 text-slate-600">
              Üben Sie mit interaktiven Aufgaben, überprüfen Sie Ihre Antworten
              und bauen Sie Ihre Deutschkenntnisse Schritt für Schritt aus.
            </p>

            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <RouterLink
                to="/login"
                class="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-100"
              >
                Zum Lernbereich
                <span aria-hidden="true">→</span>
              </RouterLink>

              <a
                href="#so-funktioniert-es"
                class="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-6 py-3.5 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              >
                Mehr erfahren
              </a>
            </div>

            <p class="mt-4 text-sm text-slate-500">
              Der Zugang erfolgt mit Ihren bereitgestellten Anmeldedaten.
            </p>
          </div>

          <div class="relative mx-auto w-full max-w-lg">
            <div class="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-blue-200/50 to-indigo-200/40 blur-2xl"></div>

            <div class="relative rounded-3xl border border-white bg-white p-5 shadow-xl shadow-blue-900/5 sm:p-7">
              <div class="flex items-start justify-between gap-4 border-b border-slate-100 pb-5">
                <div>
                  <p class="text-sm font-medium text-blue-600">
                    German Exercises
                  </p>
                  <h2 class="mt-1 text-xl font-bold text-slate-900">
                    Ihr nächster Lernschritt
                  </h2>
                </div>
                <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-xl">
                  📘
                </span>
              </div>

              <div class="space-y-4 py-5">
                <div class="flex items-center gap-4 rounded-2xl bg-slate-50 p-4">
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-lg shadow-sm">
                    ✍️
                  </span>
                  <div>
                    <h3 class="font-semibold text-slate-900">
                      Interaktiv üben
                    </h3>
                    <p class="mt-1 text-sm leading-5 text-slate-500">
                      Bearbeiten Sie Aufgaben direkt im Lernbereich.
                    </p>
                  </div>
                </div>

                <div class="flex items-center gap-4 rounded-2xl bg-slate-50 p-4">
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-lg shadow-sm">
                    ✓
                  </span>
                  <div>
                    <h3 class="font-semibold text-slate-900">
                      Antworten überprüfen
                    </h3>
                    <p class="mt-1 text-sm leading-5 text-slate-500">
                      Sehen Sie Ihre Ergebnisse nach der Bearbeitung.
                    </p>
                  </div>
                </div>

                <div class="flex items-center gap-4 rounded-2xl bg-slate-50 p-4">
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-lg shadow-sm">
                    🎯
                  </span>
                  <div>
                    <h3 class="font-semibold text-slate-900">
                      Gezielt weiterlernen
                    </h3>
                    <p class="mt-1 text-sm leading-5 text-slate-500">
                      Nutzen Sie Ihre Übungen als nächsten Schritt auf Ihrem Lernweg.
                    </p>
                  </div>
                </div>
              </div>

              <div class="rounded-2xl bg-blue-600 px-5 py-4 text-white">
                <p class="text-sm font-medium text-blue-100">
                  Bereit zum Lernen?
                </p>
                <p class="mt-1 text-base font-semibold">
                  Öffnen Sie Ihren persönlichen Lernbereich.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        id="so-funktioniert-es"
        class="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8"
      >
        <div class="max-w-2xl">
          <p class="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Lernen mit Struktur
          </p>
          <h2 class="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Ein klarer Weg zum nächsten Lernschritt
          </h2>
          <p class="mt-4 text-base leading-7 text-slate-600">
            Konzentrieren Sie sich auf Ihre Übungen und machen Sie das Lernen
            zu einem festen Bestandteil Ihres Alltags.
          </p>
        </div>

        <div class="mt-10 grid gap-5 md:grid-cols-3">
          <article class="rounded-2xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-900/5">
            <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-xl">
              📚
            </span>
            <h3 class="mt-5 text-lg font-semibold text-slate-900">
              Verschiedene Übungsformate
            </h3>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Festigen Sie Wortschatz, arbeiten Sie mit Antwortoptionen und
              trainieren Sie Sätze in unterschiedlichen Aufgabenformaten.
            </p>
          </article>

          <article class="rounded-2xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-900/5">
            <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-xl">
              ✅
            </span>
            <h3 class="mt-5 text-lg font-semibold text-slate-900">
              Ergebnisse nachvollziehen
            </h3>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Überprüfen Sie Ihre Antworten und sehen Sie nach einer Übung,
              welche Aufgaben richtig gelöst wurden.
            </p>
          </article>

          <article class="rounded-2xl border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-900/5">
            <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-xl">
              🧭
            </span>
            <h3 class="mt-5 text-lg font-semibold text-slate-900">
              Im eigenen Lernbereich
            </h3>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Melden Sie sich an, um Ihre verfügbaren Übungen zu öffnen und
              von Ihrem persönlichen Dashboard aus weiterzulernen.
            </p>
          </article>
        </div>
      </section>

      <section class="border-t border-slate-100 bg-slate-50">
        <div class="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-12 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div>
            <h2 class="text-2xl font-bold tracking-tight text-slate-900">
              Beginnen Sie mit Ihrer nächsten Übung.
            </h2>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Melden Sie sich mit Ihren Zugangsdaten an und öffnen Sie Ihren Lernbereich.
            </p>
          </div>

          <RouterLink
            to="/login"
            class="inline-flex shrink-0 items-center justify-center rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            Anmelden
          </RouterLink>
        </div>
      </section>
    </main>

    <footer class="border-t border-slate-100 bg-white">
      <div class="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-5 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <span>© {{ currentYear }} German Exercises</span>
        <span>Deutsch lernen, Schritt für Schritt.</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
const currentYear = new Date().getFullYear()
</script>
