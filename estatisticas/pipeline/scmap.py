SC={
'Araraquara':"Araraquara Bebedouro Cravinhos Jaboticabal Matão Mococa Pirassununga|Porto Ferreira|São Carlos|São José do Rio Pardo|Taquaritinga",
'Bauru':"Bauru Avaré Botucatu Garça Itápolis Jaú Marília Ourinhos Pederneiras|Lençóis Paulista|Santa Cruz do Rio Pardo",
'Campinas':"Campinas Moji-Mirim Paulínia",
'Jundiaí':"Amparo Atibaia Capivari Indaiatuba Itapira Itatiba Itu Jundiaí Salto|Bragança Paulista|Campo Limpo Paulista",
'Piracicaba':"Americana Araras Hortolândia Leme Limeira Piracicaba Sumaré|Mogi Guaçu|Rio Claro|Santa Bárbara d'Oeste|São João da Boa Vista",
'Presidente Prudente':"Adamantina Andradina Araçatuba Assis Birigui Dracena Lins Penápolis Tupã|Presidente Prudente|Presidente Venceslau|Teodoro Sampaio",
'Ribeirão Preto':"Batatais Cajuru Franca Ituverava Orlândia Sertãozinho|Ribeirão Preto|São Joaquim da Barra",
'São José do Rio Preto':"Barretos Catanduva Fernandópolis Jales Olímpia Tanabi Votuporanga|José Bonifácio|São José do Rio Preto",
'São José dos Campos':"Aparecida Caçapava Caraguatatuba Cruzeiro Guaratinguetá Jacareí Lorena Pindamonhangaba Taubaté Ubatuba|São José dos Campos|São Sebastião",
'Sorocaba':"Itanhaém Itapetininga Itapeva Itararé Piedade Registro Tatuí Tietê Sorocaba|Capão Bonito|São Roque",
}
c2sc={}
for s,v in SC.items():
  a,*b=v.split('|')
  for c in a.split()+b: c2sc[c]=s
