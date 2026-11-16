# Portal com acesso restrito ao TRT-15 (Google Apps Script)

O `Code.gs` publica o portal como **app da web do Google**. Só entra quem estiver logado com conta **@trt15.jus.br**.
O site continua sendo mantido neste repositório, que passa a ser **privado**. O app da web lê as páginas, os dados
(.json) e as imagens direto daqui. Os PDF/DOCX são copiados para uma pasta do Drive visível só para o domínio do TRT-15.
As tarefas automáticas (férias, teletrabalho, estatísticas) não mudam: continuam gravando aqui e o portal
mostra a atualização em até 5 minutos.

## Instalação (uma vez, ~15 minutos)

### 1. Token de leitura do GitHub
1. No GitHub: foto do perfil → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. Nome: `portal-apps-script`. **Resource owner**: `scpiracicaba-trt15-jus-br`. Validade: a maior permitida (anote a data para renovar).
3. **Repository access**: *Only select repositories* → `pje-dashboard`.
4. **Permissions** → *Repository permissions* → **Contents: Read-only** (nada mais).
5. Gere e copie o token (começa com `github_pat_`). Se a organização exigir aprovação, aprove em Settings da organização → Personal access tokens → Pending requests.

### 2. Projeto no Apps Script
1. Entre em <https://script.google.com> com a conta do TRT-15 → **Novo projeto**. Renomeie para `Portal SC Piracicaba`.
2. Apague o conteúdo de `Código.gs` e cole todo o conteúdo de `apps-script/Code.gs`. Salve (Ctrl+S).
3. ⚙️ **Configurações do projeto** → fuso horário `(GMT-03:00) São Paulo` → em **Propriedades do script**, adicione
   `GITHUB_TOKEN` = o token do passo 1.
4. Volte ao editor, escolha a função **configurar** no menu de funções e clique **Executar**. Autorize o acesso
   (Drive, serviços externos, gatilhos). O registro deve terminar com "Pronto". Isso testa o token, copia os PDF/DOCX
   para a pasta do Drive "Portal SC Piracicaba — arquivos" e agenda a cópia diária (21h).

### 3. Publicar
1. **Implantar** → **Nova implantação** → tipo **App da Web**.
2. **Executar como**: *Eu*. **Quem pode acessar**: a opção do **TRT-15** (qualquer pessoa do domínio trt15.jus.br).
3. **Implantar** e copie a **URL do app da web**. Esse é o novo endereço do portal.
4. Abra a URL e confira as abas (Férias, Estatísticas, normativos em PDF). Abra também numa janela anônima: deve pedir login do Google e
   recusar contas que não sejam do TRT-15.

### 4. Fechar o acesso antigo
Depois de conferir o app da web: no GitHub, **Settings** do repositório → *Danger Zone* → **Change visibility** → **Private**.
O endereço antigo (github.io) deixa de funcionar, e os dados deixam de ficar visíveis em github.com.

## Manutenção
- **Mudou o `Code.gs`?** Cole a nova versão e use **Implantar → Gerenciar implantações → editar (lápis) → Versão: Nova versão**.
  Isso mantém a mesma URL.
- **Token vencido**: o portal mostra "GitHub 401". Gere outro token (passo 1) e troque a propriedade `GITHUB_TOKEN`.
- **PDF novo no repositório**: aparece no Drive na cópia diária. Para ver na hora, rode `sincronizarArquivos` no editor.
- **Links entre páginas**: links relativos para outras páginas `.html` do repositório viram `URL?p=caminho.html` automaticamente.
