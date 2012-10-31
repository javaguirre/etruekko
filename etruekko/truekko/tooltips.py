# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _

tooltips = {}

# TODO translate this, currently we're using spanish only


# wall tab
tooltips['wall'] = _(\
u"You will see all publications of people you follow, publications"
u"from the users or the administrator of the community wall"
u"you belong. You could see publications of other users in your wall, your"
u"private messages and last offers and demands in the communities you are.")

tooltips['whats_happening'] = _(\
u"The things you publish here will be seen for anyone who follows you"
u"if you want your community to see yous posts you can write"
u"in its wall. If you want only users from your community publish"
u"in its wall and check PRIVATE ")

tooltips['private'] = _(\
"Selecting it you will see private messages you received. These messages "
"can be seen by you and the user who wrote it. If you want to publish"
"a private message to a user, go to his/her profile, post in his wall and "
"select the PRIVATE checkbox.")

tooltips['commitments'] = _(\
u"Compromises you have adquired with other user when you have a exchange with him."
u"Example: Jane and John han done an exchange, John has changes his bike with "
u"Jane in exchange of 50 kilos of oranges when they were good to be eaten."
u"Jane will be shown in his wall as MY COMPROMISES, has adquired a"
u"COMPROMISE with John and he will have in his wall COMPROMISES WITH ME. "
u"Compromises are created when you have an exchange, it's shown at the end"
u"of thw ADD COMPROMISE button, It could only be created the user who receives "
u"an offer and it has to be confirmed by the user who delivers it."
u""
u"")

tooltips['denounces'] = _(\
u"A user can sue another user if there is some kind of a problem when "
u"an exchange is made, the admin of you community receives it and solves it "
u"in the way he could. Sue status could be pending if the admin has received it "
u" but he couldn't see it, or confirmed if he did but he didn't solve the problem"
u"")

tooltips['following'] = _(\
u"In your wall will appear everything everyone is publishing, but"
u"but they won't see what you publish unless they follow you. You will be able"
u"to communicate with them directly , you just need to go to his/her profile and"
u"publish in the wall, if you want it to be PRIVATE, check the corresponding checkbox")

tooltips['followers'] = _(\
u"Estas personas ven todo lo que publicas en tu muro, pero tú no puedes ver lo "
u"que ellas publican, si quieres verlo debes de seguirlas, aun así pueden "
u"escribir en tu muro directamente")

tooltips['etruekko_wall'] = _(u"Get in touch with us and the other administrators writing here")
tooltips['channel_wall'] = _(\
u"Podrás comunicarte con los administradores de otras "
u"comunidades pertenecientes al mismo canal que tú, podrás intercambiar "
u"experiencias, iniciar posibles colaboraciones, etc...")

# people tab
tooltips['people_search'] = _(\
u"Todas las búsquedas en Etruekko se realizan "
u"por etiquetas, busca a gente por población, nombre, nick, etc... "
u"Solo debes poner la palabra que elijas y pulsar en buscar. Puedes "
u"ver todos los usuarios del sistema o únicamente tus amigos, que es "
u"la gente a la que sigues")

# services tab
tooltips['services_search'] = _(\
u"Todas las búsquedas en Etruekko se realizan "
u"por etiquetas, busca el servicio por población o palabra. Si quieres "
u"definir mas tu búsqueda usa el buscador avanzado. Una vez realizada "
u"tu búsqueda puedes hacer una oferta a alguien que tiene publicado "
u"entre sus demandas algo que tu ofreces o solicitar algo que buscas a "
u"alguien que lo tiene entre sus ofertas comenzando una negociación de "
u"intercambio")

# item tab
tooltips['items_search'] = _(\
u"Todas las búsquedas en Etruekko se realizan "
u"por etiquetas, busca el articulo por población o palabra. Si quieres "
u"definir mas tu búsqueda usa el buscador avanzado. Una vez realizada "
u"tu búsqueda puedes hacer una oferta a alguien que tiene publicado "
u"entre sus demandas algo que tu ofreces o solicitar algo que buscas a "
u"alguien que lo tiene entre sus ofertas comenzando una negociación de "
u"intercambio")

# add item tab
tooltips['item_name'] = _(\
u"Cualquier nombre que pongas aquí aparecerá en las búsquedas, "
u"p.e. si pones collar de perro, otros usuarios lo encontraran al buscar "
u"por collar o perro")

tooltips['item_price'] = _(\
u"Valora en truekkos el bien que ofertas, recuerda que la "
u"equivalencia orientativa es 1 truekko = 1 €, de esta manera otros "
u"usuarios tendrán una referencia a la hora de negociar y de decidir en "
u"sus búsquedas. Esta valoración, a la hora de negociar es secundaria, "
u"no es necesario que coincidan las valoraciones para cerrar un "
u"intercambio, p.e. si un usuario solicita un bien valorado en 15 "
u"truekkos y ofrece un servicio valorado en 10 truekkos, se puede cerrar "
u"el intercambio, ya que influyen otros factores como la valoración real "
u"de los usuarios, sus necesidades, el estado del bien, etc... No es un "
u"campo obligatorio")

tooltips['item_quantity'] = _(\
u"Incluye aquí el numero, ya que el sistema ira restando "
u"cada vez que hagas un intercambio lo que corresponda, evitando tener "
u"que crear la oferta de nuevo, p.e si publicas una oferta y pones que "
u"tienes 5 sillas, si en una transacción intercambias 2 el sistema "
u"dejará solo 3 disponibles")

tooltips['item_tags'] = _(\
u"Es muy importante que etiquetes bien tus ofertas y "
u"demandas para que sean encontradas por otros usuarios con facilidad, "
u"si publico una oferta y la nombro como collar de perro, en etiquetas "
u"pondría animales, collar, perro")

# user profile
tooltips['direct_transfer'] = _(\
u"Desde aquí  puedes hacerle un transferencia "
u"directa de truekkos a cualquier usuario")

# swap
tooltips['swap_creation'] = _(\
u"A la izquierda se muestran tus ofertas "
u"de bienes y servicios  y a la derecha todas las ofertas de bienes y "
u"servicios del usuario con el que inicies una negociación. Pulsando "
u"sobre las cajas de tu columna puedes ir marcando lo que tu ofreces y "
u"pulsando sobre las cajas de la columna con las ofertas del otro "
u"usuario iras marcando los bienes o servicios que deseas intercambiar "
u"de los que ofrece. En la caja TRUEKKOS puedes incluir los truekkos que "
u"entran en la negociación, si los pones en la caja de tu columna, "
u"significa que te los restara de tu saldo y viceversa si lo haces en la "
u"caja del otro usuario."
u"<br/>"
u"<br/>"
u"Cuando inicies una negociación o te hagan una oferta, aparecerá un "
u"aviso en tu muro, veras en verde la propuesta que has hecho o te han "
u"hecho, el usuario que recibe la oferta podrá modificarla incluyendo o "
u"quitando bienes, servicios y truekkos tanto de los que tu ofreces como "
u"de los que el ofrece")

tooltips['swap_mode'] = _(\
u"Puedes pactar la forma de entrega de artículos o "
u"prestación de servicios, no es un campo obligatorio, en el caso de "
u"intercambio por correo postal, la aplicación te mostrara la dirección "
u"de ambos usuarios, esta se rellena desde tus preferencias. En el caso "
u"de entrega mediante mensajería, no olvides pactar quien asume los "
u"gastos de envío")

tooltips['swap_accept'] = _(\
u"Si pulsas aceptar, supone que has cerrado un intercambio "
u"en las condiciones pactada hasta ese momento. Solo puede aceptar el "
u"usuario que recibe una oferta o contraoferta. Si pulsas hacer oferta "
u"enviaras una propuesta de negociación a otro usuario, o bien una "
u"contraoferta, una negociación puede tener tantas contraofertas como "
u"los usuarios crean necesarias antes de cerrar el intercambio. Si "
u"pulsas cancelar significa que no te interesa la propuesta que un "
u"usuario te ha hecho")

# admin groups
tooltips['admin_group_edit'] = _(\
u"Cambia tu avatar, información URL,  cualquier otra "
u"información de tu comunidad que desees")

tooltips['admin_group_edit_members'] = _(\
u"Desde aquí podrás cambiar el rol de un usuario de "
u"miembro a administrador o viceversa, expulsarlo de tu comunidad o "
u"eliminarlo. Si lo expulsas de tu comunidad no borrar sus datos de "
u"registro, si lo eliminas borraras todos sus datos de registro"
u"<br/>"
u"<br/>"
u"Como administrador también podrás editar el perfil de los usuarios de "
u"tu comunidad, con el fin de poder incluir en el sistema a personas que "
u"no tienen acceso a internet, a las que puedes crearles su perfil y "
u"editárselo")

tooltips['admin_group_add_member'] = _(\
u"Desde el botón AÑADIR MIEMBRO podrás añadir nuevos miembros que estén "
u"registrados en Etruekko pero no en tu comunidad, así como crear el "
u"perfil de un nuevo usuario")

tooltips['admin_group_goto_channel'] = _(\
u"Desde IR AL CANAL ... podrás comunicarte con los administradores de "
u"otras comunidades pertenecientes al mismo canal que tu, podrás "
u"intercambiar experiencias, iniciar posibles colaboraciones, etc...")
