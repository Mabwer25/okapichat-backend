// Service Worker pour OkapiChat PWA
// Cache et fonctionnalités offline

const CACHE_NAME = 'okapichat-v1.0.0';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/style.css',
    '/js/app.js',
    '/js/auth.js',
    '/js/posts.js',
    '/js/calls.js',
    '/js/mobile.js',
    '/js/languages.js',
    '/js/profiles.js',
    '/js/messaging.js',
    '/manifest.json',
    '/images/icon-192.png',
    '/images/icon-512.png'
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
    console.log('🔄 Service Worker: Installation');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('🔄 Service Worker: Cache ouvert');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('✅ Service Worker: Assets mis en cache');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('❌ Service Worker: Erreur installation', error);
            })
    );
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
    console.log('🔄 Service Worker: Activation');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((cacheName) => {
                            return cacheName !== CACHE_NAME;
                        })
                        .map((cacheName) => {
                            console.log('🗑️ Service Worker: Suppression ancien cache', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                console.log('✅ Service Worker: Activé');
                return self.clients.claim();
            })
    );
});

// Stratégie de cache: Cache First pour les assets, Network First pour les données
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Ignorer les requêtes non-HTTP
    if (!request.url.startsWith('http')) {
        return;
    }
    
    // Ignorer les requêtes Supabase (toujours réseau)
    if (url.hostname.includes('supabase.co')) {
        return;
    }
    
    // Stratégie Cache First pour les assets statiques
    if (STATIC_ASSETS.some(asset => request.url.includes(asset))) {
        event.respondWith(
            caches.match(request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        console.log('📦 Cache: Asset trouvé', request.url);
                        return cachedResponse;
                    }
                    
                    console.log('🌐 Réseau: Téléchargement asset', request.url);
                    return fetch(request)
                        .then((response) => {
                            if (response.ok) {
                                const responseClone = response.clone();
                                caches.open(CACHE_NAME)
                                    .then((cache) => {
                                        cache.put(request, responseClone);
                                    });
                            }
                            return response;
                        });
                })
                .catch(() => {
                    console.log('❌ Offline: Asset non disponible', request.url);
                    // Retourner une page offline personnalisée si nécessaire
                    if (request.destination === 'document') {
                        return caches.match('/offline.html');
                    }
                })
        );
    } else {
        // Stratégie Network First pour les données dynamiques
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Mettre en cache les réponses valides
                    if (response.ok && request.method === 'GET') {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(request, responseClone);
                            });
                    }
                    return response;
                })
                .catch(() => {
                    console.log('🌐 Réseau: Échec, tentative cache', request.url);
                    return caches.match(request);
                })
        );
    }
});

// Gestion des notifications push
self.addEventListener('push', (event) => {
    console.log('🔔 Push notification reçue');
    
    const options = {
        title: 'OkapiChat',
        body: 'Nouveau message reçu !',
        icon: '/images/icon-192.png',
        badge: '/images/badge-72.png',
        vibrate: [200, 100, 200],
        data: {
            url: '/'
        },
        actions: [
            {
                action: 'open',
                title: 'Ouvrir'
            },
            {
                action: 'close',
                title: 'Fermer'
            }
        ]
    };
    
    if (event.data) {
        try {
            const pushData = event.data.json();
            options.title = pushData.title || options.title;
            options.body = pushData.body || options.body;
            options.data = { ...options.data, ...pushData.data };
        } catch (error) {
            console.error('❌ Erreur parsing push data:', error);
        }
    }
    
    event.waitUntil(
        self.registration.showNotification(options.title, options)
    );
});

// Gestion des clics sur notifications
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 Notification cliquée');
    
    event.notification.close();
    
    if (event.action === 'close') {
        return;
    }
    
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Chercher un onglet déjà ouvert
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.navigate(urlToOpen);
                        return client.focus();
                    }
                }
                
                // Ouvrir un nouvel onglet
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Synchronisation en arrière-plan
self.addEventListener('sync', (event) => {
    console.log('🔄 Synchronisation en arrière-plan:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

// Fonction de synchronisation
async function doBackgroundSync() {
    try {
        console.log('🔄 Exécution synchronisation en arrière-plan');
        
        // Ici, on pourrait synchroniser les données offline
        // Par exemple, envoyer les posts créés hors ligne
        
        // Notifier les clients de la synchronisation
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'BACKGROUND_SYNC_COMPLETE'
            });
        });
        
        console.log('✅ Synchronisation terminée');
        
    } catch (error) {
        console.error('❌ Erreur synchronisation:', error);
    }
}

// Gestion des messages depuis l'app principale
self.addEventListener('message', (event) => {
    console.log('📨 Message reçu du client:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

// Mise à jour du cache en arrière-plan
self.addEventListener('backgroundfetch', (event) => {
    console.log('🔄 Background fetch:', event.tag);
    
    if (event.tag === 'update-cache') {
        event.waitUntil(updateCacheInBackground());
    }
});

async function updateCacheInBackground() {
    try {
        console.log('🔄 Mise à jour cache en arrière-plan');
        
        const cache = await caches.open(CACHE_NAME);
        await cache.addAll(STATIC_ASSETS);
        
        console.log('✅ Cache mis à jour en arrière-plan');
        
    } catch (error) {
        console.error('❌ Erreur mise à jour cache:', error);
    }
}

console.log('🔄 Service Worker OkapiChat initialisé');