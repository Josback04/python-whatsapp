from flask import current_app # Pour accéder à la config (DB credentials)
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.database.database import get_user_data
from app.config import logging




def ask_ai(user_id):
    user_answers= get_user_data(user_id)

   

    if user_answers:
        formatted_answers= "\n".join([f"**{entry['question']}** : {entry['answer']}" for entry in user_answers])
    else:
        formatted_answers = "Aucune reponse trouvée"


    prompt=f"""
    Analyse ces données et génère un modèle de Business Modèle Structuré basé sur ces données, dans ta réponse évite les réponses génériques du genre 'voici le business modèle pour l'utilisateur etc.' parle à la première personne emploi le 'Je' dans tes phrases  : {formatted_answers}
    Voici un prompt que vous pouvez utiliser pour demander à un modèle linguistique de répondre aux questions d'un utilisateur en suivant la mise en forme du document "FORMAT BP 2_085015 (1).docx" :

**Prompt :**

"Vous êtes un assistant chargé de répondre aux questions d'un utilisateur en suivant la mise en forme du document ci-dessous, qui décrit la structure d'un business plan. Veuillez utiliser cette structure comme guide pour organiser vos réponses.

**Structure du document :**

**Génération de la valeur**

**I.1. Présentation de l’entrepreneur**

*   C’est ta présentation dans le détail (ou votre présentation si c’est pour 2 ou plus) :
    *   Qui est l’entrepreneur (Nom, porte-nom, prénom, Age,..) , son expérience (Etude faite ?, formation suivie en rapport de son travail, combien de temps que vous êtes dans ce travail ?), ses motivations (pourquoi tu fais ce travail ?), son histoire (comment tu as commencé ?, où ?) ? Quelles sont ses limites (difficultés rencontrées dans ton travail) et comment compte-t-il le résoudre ? Quels sont ses points forts ( tes atouts) et comment compte-t-il l’utiliser dans l’entreprise ?
    *   De qui se compose son entourage immédiat ou proche qui peut le soutenir (pas seulement financièrement) dans la concrétisation de son projet (Nom, poste nom, prénom, ce qu’il fait, comment ou en quoi il va te soutenir) .
    *   A-t-il un associé ? Si oui, qui est-il (Nom, Post-nom, prénom, Age), son expérience, ses motivations ? (ce qu’il fait, comment ou en quoi il va te soutenir). Qui sont les autres personnes qui sont autour de lui et en quoi leur aide peut lui être utile pour son projet ?

**I.2. Présentation de l’entreprise**

*   a) Informations générales sur la PME
    *   Nom de l’entreprise
    *   Forme juridique
    *   Siège sociale : (adresse juridique de l’entreprise)
    *   Coordonnées bancaires
    *   Localisation de l’entreprise : lieu d’implantation de l’entreprise
*   b) Description de l’entreprise
*   c) Objectifs de l’entreprise
*   d) Stade d’avancement de l’entreprise ou du projet
    *   Décrivez ce qui a été fait et les projets à mener dans le futur ( : décrivez les activités déjà menées et votre positionnement (amorçage, prototypage, développement)
    *   Parlez du niveau de maturité de la PME / du projet
*   e) Présentation de l’équipe managériale
    *   Décrivez l’organigramme et l’organisation des ressources humaines,
    *   Présenter les associés de la PME ainsi que leurs parts sociales
*   f) Analyse SWOT de l’entreprise : Forces-Faiblesses, Opportunités-Menaces

**I.3.Présentation de l’offre de produit(s) ou service(s)**

*   la description de mon offre (Produit / Service) ;
*   Donner plus de détail sur ton produit/Service :
    *   Que propose-t-il comme offre (Ce que tu fais ? ton produit ou ton service à offrir) ? Noms du / des produit (s) ou service (s), Comment se présente- t- elle ? (l’emballage, quantité, couleur,…), quelles sont ces valeurs nutritives ?, ces caractéristiques ?, comment ton produit/service fonctionne ?.
    *   Besoins identifiés sur les marché auxquels répond votre offre,
    *   A quel besoin répond précisément le bien ou la prestation ?
    *   Quelle est son utilité ?
    *   Mode d’utilisation du bien ou service ?
    *   Décrire l’usage et le mode de fonctionnement initialement envisagés doit amener à se demander s’ils sont conformes aux attentes actuelles des consommateurs (gain de temps, simplicité, gain de place, économie, nouveauté, etc.).
    *   Comment il faut l’utiliser ?
    *   Faudrait-il éduquer les consommateurs ?
    *   Faudrait-il des conditions spécifiques pour son utilisation ?
*   l’innovation de mon offre ;
    *   Quels sont les atouts (avantages) de cette offre (en quoi ton offre est différente des autres) ?
    *   Quels sont les points forts de votre produit, service ou concept ? : Il s'agit des performances attendues, de l'avantage concurrentiel qui sera détenu.
*   Etude de la concurrence ;
    *   Quels sont les produits ou services directement concurrents (Lister)? Quels sont les produits ou services indirectement concurrents, c'est à dire qui peut se substituer ?
    *   Présenter la concurrence directe et indirecte (lister les concurrents et les décrire)
    *   Lister les points forts et les points faibles de la concurrence
    *   Caractéristique de l'offre et des entreprises concurrentes Analyser de manière détaillée les concurrents directs et indirects : Qui sont-ils ? Où sont-ils ? Que proposent-ils ? A quels prix ? Comment vendent-ils ? Comment communiquent-ils ? Quels sont leurs résultats financiers ? A qui vendent-ils ? Quels sont leurs avantages concurrentiels ? Quelle est leur part de marché ? Les clients / utilisateurs sont-ils satisfaits ? Etc.
    *   Présenter ce qui te différencie de chaque concurrent ? ,
*   Mode de conservation ;
    *   Endroit et moyen de conservation.
*   La durée de vie de mon produit ;
*   La Game que j’offre (différents produits ou services à offrir)
*   Clients
    *   Qui sont les clients (Quel type de clientèle pensez-vous pouvoir toucher ?) ? Quelle est la cible principale ? (donnez une description de ce que pourrait être votre cible principale). Où sont vos clients ?
    *   Choix de segments de clientèle
    *   Expliquer quels segments de clientèle vont constituer la cible du projet d’entreprise / de la PME et pourquoi ce choix ;
    *   Expliquer dans les grandes lignes, le positionnement stratégique du projet d’entreprise / de la PME
    *   Comportement du client et de l'utilisateur Qui sont-ils ? A quelle occasion achète-t-il (le client) ou utilise-t-il (l'utilisateur) le produit et/ou le service que vous proposez ? Comment ? Où ? Pourquoi ? Sont-t-ils satisfaits ? Quelles sont leurs motivations ? Quels sont leurs freins ? Quelle est leur perception du produit et/ou du service ? Quelles sont les caractéristiques du produit et/ou du service qui pourraient favoriser l'acte d'achat ou d'utilisation (prix, taille, mode d'achat, etc.) ? Quel besoin satisfait ou vient résoudre votre produit auprès de ces clients ? Combien sont-ils prêts à payer ?
    *   Les acteurs
    *   Qui sont les principaux acteurs sur le marché ? Les concurrents, les clients, les utilisateurs, les acheteurs, les prescripteurs, les producteurs, les distributeurs, les sous-traitants, etc.
    *   Modes de vente
    *   Les modes de vente sont nombreux (boutique, force de vente, vente par correspondance, marchés forains, prescripteurs, vente en réunions, par Internet, etc.).
    *   Quelles sont les avantages et les contraintes éventuelles liées à votre produit, service ou concept ?
    *   Tableau :

Caractéristiques du produit ou service ,Avantages particuliers ,Contraintes particulières

*   I.3 . Source de mon idée c.à.d. d’où vient mon idée de faire :
    *   Le produit ;
    *   L’entreprise
    *   D’où vient cette idée ?
*   I.4. Comment je fais pour avoir mon produit ou comment je fais pour fabriquer mon produit ?
    *   La description de mon processus de fabrication
    *   La description du processus d’approvisionnement des Matières Premières (d’où vient –elle ? comment je l’amène jusqu’à l’entreprise ? sous quelle condition de conservation ?)
    *   Quelles sont les avantages et les contraintes liées à la production?
    *   Tableau :

Caractéristiques liées à la production ,Avantages particuliers ,Contraintes particulières

Approvisionnements ,,
Processus de fabrication ,,
Conditionnement ,,

*   Quelles sont les personnes avec qui je veux travailler et leurs taches respectives ?
*   Le délai de fabrication du produit ( et capacité de production)
*   Localisation de mon entreprise et pourquoi là-bas ?
*   I.5. Environnement du projet
    *   Sociale : Quelle est la culture ? Quelles sont les valeurs et les normes ? Quel est le niveau d'éducation ? Comment évolue la démographie ? Quelles sont les habitudes de consommation ?
    *   Ecologique : Quelle est la sensibilité aux enjeux du développement durable ? Quelles sont les mesures prises en faveur de l'environnement ? Quel traitement est réservé aux déchets ?

**Rémunération De La Valeur**

**II.1. Volume de revenu (Argent)**

*   Tableau des investissements (Lister les équipements avec le prix)
*   Tableau des amortissements
*   Calcul des couts et prix (Lister tout ce qui entre dans un produit ou service, savoir leur quantité, le prix)
*   Prévision de production et vente (Réaliste et pessimiste)
*   Présentation des Marges et des Taxes
*   Tableau de marges bénéficiaires avec une production constante

Eléments de marge bénéficiaire,Mois1,Mois2 ,3,4,5,6,7,8,9,10,11,12,Total/an
Q,,,,,,,,,,,,,
PVUHT,,,,,,,,,,,,,
CA : Chiffre d’affaires (Q x PU),,,,,,,,,,,,,
CR : Coût de revient ,,,,,,,,,,,,,
Marges bénéficiaires (=CA-CR),,,,,,,,,,,,,

*   Une phrase de commentaire sur les marges espérées
*   Tableau de seuil de rentabilité (tableau de résultat différentiel) : voir module sur les coûts

Eléments de seuil de rentabilité d’exploitation,Montant/ an ,%
CA,,
CV,,
CF,,
R,,
SR,,
Point mort,,
Levier opérationnel,,

*   Une phrase de commentaire sur le seuil de rentabilité et le point mort

**II.2. Source de revenu**

*   Vente de produit
*   Emprunt
*   Mon propre apport ou celui de mes associés
*   L’aide de l’I&F entrepreneuriat

Besoins en financement,Montant,Apports souhaités,Montant
Equipement total,,Moi-même (Nom),
Besoin du départ pour financer l’exploitation,,X,
,,Y,
,,Z,
Besoin total de financement,,Financement total à apporter,

*   Au total, notre entreprise exige un financement de … dont x montant pour l’acquisition des équipements et Y montant pour commencer l’exploitation pour … en matière première, main d’œuvre, distribution, etc. Pour les financer, nous apportons nous-mêmes…et recherchons auprès de … et de …

**II.3. Canaux de revenu :**

*   Type de distribution
*   Le prix au producteur combien ?
*   Le prix aux consommateurs final combien ?
*   Le prix aux détaillants combien ?
*   Le prix aux grossistes combien ?
*   Le prix aux demi grossistes combien ?
*   Marketing mixte
*   Présenter la politique marketing générale :
    *   Choix du nom, du logo et des couleurs,
    *   Choix du message, du slogan.
*   Politique de produit :
    *   Dire de quoi est composé votre produit (caractéristique), comment est-il conditionné ou présenté et pour qui ? Est-il offert en gamme ?a-t-il un nom qui signifie quoi ? Comment l’utilise-t-on, quand et où ? Quelles sont les précautions à prendre quand on l’utilise ? Précautions à prendre quand on le conserve.
*   Politique de prix :
    *   Dire quel est le prix unitaire de votre produit ? Quelle est la marge unitaire bénéficiaire ? Est-ce un prix égal au prix du marché si ce produit existe déjà ? Si le prix est différent, dire pourquoi ? Est-ce un prix fixé en fonction de votre coût de revient unitaire ? Quel est le prix de vente unitaire hors taxe ? Quel est le prix unitaire toute taxe confondue ?
*   Politique de distribution :
    *   Comment allez-vous écouler vos produits ? Où seront vos points de vente ? Comment vos clients peuvent-ils accéder facilement à vos produits ? Vos clients sont-ils catégorisés en grossistes ? En détaillants ? En clients finals ? En âge ? En sexe ? Etc. Quelles sont vos modalités de paiement ? Quel est votre délai de livraison moyen ?
*   Politique de communication :
    *   Avez-vous prévu un cadeau pour une certaine quantité achetée ? Allez-vous exposé vos produits pour leurs promotions? Comment allez-vous faire pour faire connaitre votre produit et combien ça peut coûter en référence à votre coût de revient unitaire ?

**PARTAGE DE LA VALEUR**

*   a) Analyse des éléments clés de succès et facteurs stratégiques de risque
    *   Q1.Quels sont les éléments (événements ou circonstances) pouvant favoriser la réussite de votre projet ?
    *   Q2. Comment comptez-vous utiliser ces éléments en votre faveur ?
    *   Q3. Quels sont les éléments (événements ou circonstances) pouvant bloquer la réussite ou la réalisation de votre projet ?
    *   Q4. Comment comptez-vous transformer ces éléments en facteurs favorables ?
*   b) Matrice des parties prenantes
    *   Q1. Quelles sont les personnes (physiques ou morales) qui peuvent être impliquées dans la réalisation de ce projet ? Donner pour chacune de ces personnes les renseignements complets (noms, adresse, téléphone, etc.)
    *   Q2. Citer pour chaque personne identifiée ce que pourra être son apport (argent, équipements, matières premières, savoir ou autre)
    *   Q3. Identifier pour chacune de ces personnes ce que pourra être ses attentes lors de la réalisation de ce projet (ce que chaque va gagner lors de la réalisation du projet)
    *   Q4. Définir le pouvoir ou le rôle de chacune de ces personnes dans votre future entreprise

**III.1. Avec la banque**

*   Tableau d’amortissement d’emprunt
*   Tableau de marge bénéficiaire net

**III.2. Le partage du %de M.O**

Personnel,Fonction ou tache,% au total M.O,Montant total salaire,Salaire Brut (5=3*4)

**III.3. Avec l’état et autres (DGI, DGRAD….)**

**III.4 . I&F entrepreneuriat**

**III.5. Bio val**


**Gestion de fonds**

*   Salaire à verser au compte courant1
*   Le coût fixe(CF) à verser au compte épargne1
*   La TVA, La commission pub et La marge bénéficiaire net à verser au compte épargne2

**Annexes :**

*   Tableau : Avantages et contraintes du produit ou service (Boite à outil entrepreneurial – Evaluer son idée)

Caractéristiques du produit ou service ,Avantages particuliers ,Contraintes particulières
Complexe ,,
Innovant ,,
Fragile ,,
Périssable ,,
Dangereux ,,
Polluant ,,
Copiable ,,
Très couteux ,,
A usage unique ,,
Saisonnier ,,
Susceptible d’être rapidement obsolète ,,
Mode de conservation ,,

*   Avantages et contraintes liées à la production (Boite à outil entrepreneurial – Evaluer son idée)
    *   Tableau :

Caractéristiques liées à la production ,Avantages particuliers ,Contraintes particulières
Approvisionnements ,,
Processus de fabrication ,,
Conditionnement ,,

*   Etude de marché"

**Consignes supplémentaires :**

*   Utilisez un ton professionnel et concis.
*   Respectez la mise en forme (titres, sous-titres, listes
"""
        
    client = genai.Client(api_key=os.environ.get("GEMINI_KEY"))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(system_instruction="Tu es un coach pour les PME en élaboration des business plan et plan d'affaire."),
        contents=prompt
    )

   

    return response.text


