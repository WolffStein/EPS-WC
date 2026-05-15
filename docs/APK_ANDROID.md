# APK Android

Este projeto agora possui uma base Android em `android-apk/` para gerar um APK simples do
`Assistente de Apreensao`.

## Estrategia adotada

Como o backend principal continua em Django, o APK foi estruturado como um app Android nativo
com `WebView`.

Esse app:

- abre o sistema web dentro do Android
- permite configurar a URL do backend no proprio app
- aceita trafego HTTP para testes locais na rede
- suporta upload de arquivo e captura por camera via seletor do Android

## Onde esta o projeto Android

`android-apk/`

Arquivos principais:

- `android-apk/app/src/main/java/br/com/epswc/apreensao/MainActivity.kt`
- `android-apk/app/src/main/AndroidManifest.xml`
- `android-apk/app/src/main/res/layout/activity_main.xml`
- `android-apk/app/build.gradle.kts`

## Como usar no Android Studio

1. Abra o Android Studio.
2. Escolha `Open`.
3. Selecione a pasta `android-apk`.
4. Aguarde o sync do Gradle.
5. Ajuste o SDK se o Android Studio pedir.
6. Rode em um emulador ou aparelho fisico.

## Como gerar o APK

No Android Studio:

1. `Build`
2. `Build Bundle(s) / APK(s)`
3. `Build APK(s)`

O Android Studio vai gerar um APK de debug inicialmente.

## Como apontar para o backend

Ao abrir o app pela primeira vez, ele pede a URL do backend Django.

Exemplos:

- teste local na mesma rede: `http://192.168.1.11:8000/`
- ambiente publicado: `https://seu-dominio.com/`

O valor fica salvo no proprio app, e pode ser alterado depois pelo botao `Servidor`.

## Fluxo recomendado para testes

1. No computador, suba o backend Django.
2. Garanta que o celular e o computador estao na mesma rede.
3. Descubra o IP local do computador.
4. No APK, informe `http://SEU_IP:8000/`.
5. Entre com o usuario do sistema e teste o fluxo de captura.

## Permissoes importantes

O app ja foi preparado com:

- `INTERNET`
- `CAMERA`

Tambem foi configurado:

- `usesCleartextTraffic=true`
- `network_security_config` liberando HTTP para testes locais
- `FileProvider` para camera e upload

## Limitacoes atuais

- este ambiente nao tem `Java` nem `Android Studio`, entao eu nao consegui compilar o APK daqui
- a estrutura foi preparada para abrir e buildar no Android Studio da equipe
- se quiser publicar em loja, ainda vale revisar assinatura, icones finais e hardening

## Proximo passo sugerido

Depois de gerar o primeiro APK, o ideal e testar:

1. login
2. criar operacao
3. abrir captura rapida
4. enviar imagem
5. validar autopreenchimento da Gemini dentro do app
