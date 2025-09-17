#!/usr/bin/env python3
"""
Injecteur SOAP avec variabilisation automatique
Envoie des messages SOAP aléatoires avec génération d'UUID et variables personnalisées
"""

import os
import re
import uuid
import random
import logging
import requests
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time

class SOAPInjector:
    def __init__(self, soap_dir: str, endpoint: str, timeout: int = 30):
        """
        Initialise l'injecteur SOAP
        
        Args:
            soap_dir: Répertoire contenant les fichiers SOAP
            endpoint: URL de l'endpoint SOAP
            timeout: Timeout des requêtes HTTP
        """
        self.soap_dir = Path(soap_dir)
        self.endpoint = endpoint
        self.timeout = timeout
        self.soap_files = []
        self.session = requests.Session()
        
        # Configuration du logging
        self._setup_logging()
        
        # Chargement des fichiers SOAP
        self._load_soap_files()
    
    def _setup_logging(self):
        """Configure le système de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_soap_files(self):
        """Charge la liste des fichiers SOAP disponibles"""
        if not self.soap_dir.exists():
            raise FileNotFoundError(f"Répertoire SOAP introuvable: {self.soap_dir}")
        
        # Cherche tous les fichiers XML dans le répertoire
        self.soap_files = list(self.soap_dir.glob("*.xml"))
        
        if not self.soap_files:
            raise ValueError(f"Aucun fichier XML trouvé dans: {self.soap_dir}")
        
        self.logger.info(f"Chargé {len(self.soap_files)} fichier(s) SOAP depuis {self.soap_dir}")
        for file in self.soap_files:
            self.logger.info(f"  - {file.name}")
    
    def _generate_variables(self) -> Dict[str, str]:
        """
        Génère les variables de remplacement
        
        Returns:
            Dictionnaire des variables avec leurs valeurs
        """
        now = datetime.now()
        
        variables = {
            # UUID
            'UUID': str(uuid.uuid4()),
            'UUID_UPPER': str(uuid.uuid4()).upper(),
            'UUID_NO_DASH': str(uuid.uuid4()).replace('-', ''),
            
            # Timestamps
            'TIMESTAMP': now.strftime('%Y-%m-%dT%H:%M:%S'),
            'TIMESTAMP_MS': now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
            'DATE': now.strftime('%Y-%m-%d'),
            'TIME': now.strftime('%H:%M:%S'),
            'EPOCH': str(int(now.timestamp())),
            
            # Identifiants aléatoires
            'RANDOM_ID': str(random.randint(100000, 999999)),
            'RANDOM_ALPHA': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8)),
            'RANDOM_ALPHANUM': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10)),
        }
        
        return variables
    
    def _replace_variables(self, content: str, variables: Dict[str, str]) -> str:
        """
        Remplace les variables dans le contenu SOAP
        
        Format supporté: {{VARIABLE_NAME}}
        
        Args:
            content: Contenu SOAP original
            variables: Variables à remplacer
            
        Returns:
            Contenu avec variables remplacées
        """
        result = content
        
        for var_name, var_value in variables.items():
            pattern = f"{{{{{var_name}}}}}"
            result = result.replace(pattern, var_value)
        
        return result
    
    def _select_random_soap(self) -> Path:
        """Sélectionne un fichier SOAP au hasard"""
        return random.choice(self.soap_files)
    
    def _load_soap_content(self, soap_file: Path) -> str:
        """Charge le contenu d'un fichier SOAP"""
        try:
            with open(soap_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Erreur lecture {soap_file.name}: {e}")
            raise
    
    def _send_soap_request(self, content: str, soap_file: str) -> bool:
        """
        Envoie une requête SOAP
        
        Args:
            content: Contenu SOAP à envoyer
            soap_file: Nom du fichier SOAP pour le logging
            
        Returns:
            True si succès (HTTP 200), False sinon
        """
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '""',  # SOAPAction vide par défaut
        }
        
        try:
            self.logger.info(f"Envoi SOAP [{soap_file}] vers {self.endpoint}")
            
            response = self.session.post(
                self.endpoint,
                data=content.encode('utf-8'),
                headers=headers,
                timeout=self.timeout
            )
            
            # Vérification du statut HTTP
            if response.status_code == 200:
                self.logger.info(f"✓ Succès [{soap_file}] - HTTP {response.status_code} - {len(response.content)} bytes")
                return True
            else:
                self.logger.warning(f"✗ Échec [{soap_file}] - HTTP {response.status_code} - {response.reason}")
                self.logger.debug(f"Réponse: {response.text[:200]}...")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"✗ Timeout [{soap_file}] - Délai dépassé ({self.timeout}s)")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"✗ Erreur connexion [{soap_file}] - Endpoint inaccessible")
            return False
        except Exception as e:
            self.logger.error(f"✗ Erreur inattendue [{soap_file}] - {type(e).__name__}: {e}")
            return False
    
    def inject_single(self) -> bool:
        """
        Injecte un seul message SOAP
        
        Returns:
            True si succès, False sinon
        """
        # Sélection aléatoire d'un fichier SOAP
        soap_file = self._select_random_soap()
        
        # Chargement du contenu
        content = self._load_soap_content(soap_file)
        
        # Génération des variables
        variables = self._generate_variables()
        
        # Remplacement des variables
        processed_content = self._replace_variables(content, variables)
        
        # Log des variables utilisées (debug)
        self.logger.debug(f"Variables générées: {list(variables.keys())}")
        
        # Envoi de la requête
        return self._send_soap_request(processed_content, soap_file.name)
    
    def inject_multiple(self, count: int, delay: float = 0.0) -> Dict[str, int]:
        """
        Injecte plusieurs messages SOAP
        
        Args:
            count: Nombre de messages à envoyer
            delay: Délai entre chaque envoi (secondes)
            
        Returns:
            Statistiques des envois
        """
        stats = {'success': 0, 'failed': 0, 'total': count}
        
        self.logger.info(f"Début injection de {count} message(s) SOAP")
        start_time = time.time()
        
        for i in range(1, count + 1):
            self.logger.info(f"--- Injection {i}/{count} ---")
            
            success = self.inject_single()
            
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # Délai entre les envois
            if delay > 0 and i < count:
                self.logger.info(f"Attente {delay}s avant prochain envoi...")
                time.sleep(delay)
        
        elapsed = time.time() - start_time
        success_rate = (stats['success'] / stats['total']) * 100
        
        self.logger.info("="*50)
        self.logger.info(f"Injection terminée en {elapsed:.2f}s")
        self.logger.info(f"Succès: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        self.logger.info(f"Échecs: {stats['failed']}/{stats['total']}")
        self.logger.info("="*50)
        
        return stats


def main():
    parser = argparse.ArgumentParser(description='Injecteur SOAP avec variabilisation')
    parser.add_argument('endpoint', help='URL de l\'endpoint SOAP')
    parser.add_argument('--soap-dir', '-d', default='./soap_templates', 
                       help='Répertoire contenant les fichiers SOAP (défaut: ./soap_templates)')
    parser.add_argument('--count', '-c', type=int, default=1,
                       help='Nombre de messages à envoyer (défaut: 1)')
    parser.add_argument('--delay', '-w', type=float, default=0.0,
                       help='Délai entre envois en secondes (défaut: 0)')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                       help='Timeout des requêtes HTTP (défaut: 30s)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbose (debug)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        injector = SOAPInjector(args.soap_dir, args.endpoint, args.timeout)
        
        if args.count == 1:
            success = injector.inject_single()
            exit(0 if success else 1)
        else:
            stats = injector.inject_multiple(args.count, args.delay)
            exit(0 if stats['failed'] == 0 else 1)
            
    except Exception as e:
        logging.error(f"Erreur fatale: {e}")
        exit(1)


if __name__ == "__main__":
    main()