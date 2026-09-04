# -*- coding: utf-8 -*-
"""Modèle métier pur Python d'un carnet de publication dynamique.

Ce modèle est indépendant de Revit et de WPF. Il décrit la configuration
persistante d'un carnet dynamique sans déclencher sa résolution ni sa publication.
"""

from models.dynamic_rule import DynamicRuleDefinition


class DynamicPublicationSet(object):
    """Décrit un carnet manuel ou dynamique avec un contrat persistable."""

    SCHEMA_VERSION = 1
    TYPES = ("manual", "dynamic")

    def __init__(self, name, set_id=None, set_type="dynamic", folder_id=None,
                 source=None, output_directory=None, filename_template_id=None,
                 persistent=True, publication_settings=None,
                 rule_definition=None, exclusions=None, snapshot_key=None):
        if not name:
            raise ValueError("Un carnet dynamique doit avoir un nom.")
        if set_type not in self.TYPES:
            raise ValueError("Type de carnet inconnu : {0}".format(set_type))

        self.id = set_id
        self.name = name
        self.set_type = set_type
        self.folder_id = folder_id
        self.source = source
        self.output_directory = output_directory
        self.filename_template_id = filename_template_id
        self.persistent = bool(persistent)
        self.publication_settings = publication_settings
        self.rule_definition = rule_definition if set_type == "dynamic" else None
        self.exclusions = list(exclusions or []) if set_type == "dynamic" else []
        self.snapshot_key = snapshot_key if set_type == "dynamic" else None

    @property
    def is_dynamic(self):
        return self.set_type == "dynamic"

    @property
    def is_manual(self):
        return self.set_type == "manual"

    def validate(self):
        """Retourne une liste d'erreurs de modèle, sans lever d'exception."""
        errors = []
        if not self.name:
            errors.append("NAME_REQUIRED")
        if self.set_type not in self.TYPES:
            errors.append("INVALID_TYPE")
        if self.is_dynamic and not isinstance(self.rule_definition, DynamicRuleDefinition):
            errors.append("DYNAMIC_RULE_DEFINITION_REQUIRED")
        if self.is_dynamic and self.snapshot_key is not None and not self.snapshot_key:
            errors.append("INVALID_SNAPSHOT_KEY")
        return errors

    def to_dict(self):
        """Sérialise uniquement la configuration, jamais les objets Revit."""
        data = {
            "schema_version": self.SCHEMA_VERSION,
            "id": self.id,
            "name": self.name,
            "set_type": self.set_type,
            "folder_id": self.folder_id,
            "source": self.source,
            "output_directory": self.output_directory,
            "filename_template_id": self.filename_template_id,
            "persistent": self.persistent,
            "publication_settings": self.publication_settings,
        }
        if self.is_dynamic:
            data["rule_definition"] = self.rule_definition.to_dict()
            data["exclusions"] = list(self.exclusions)
            data["snapshot_key"] = self.snapshot_key
        return data


class DynamicPublicationSetSerializer(object):
    """Sérialise, désérialise et migre les carnets dynamiques."""

    CURRENT_VERSION = DynamicPublicationSet.SCHEMA_VERSION

    @classmethod
    def serialize(cls, publication_set):
        if not isinstance(publication_set, DynamicPublicationSet):
            raise TypeError("Le carnet doit être un DynamicPublicationSet.")
        errors = publication_set.validate()
        if errors:
            raise ValueError("Carnet invalide : {0}".format(", ".join(errors)))
        return publication_set.to_dict()

    @classmethod
    def deserialize(cls, data):
        if not isinstance(data, dict):
            raise TypeError("Les données du carnet doivent être un dictionnaire.")
        migrated = cls.migrate(data)
        set_type = migrated.get("set_type", "dynamic")
        rule_definition = None
        if set_type == "dynamic":
            rule_definition = cls._rule_definition_from_dict(migrated.get("rule_definition"))
        result = DynamicPublicationSet(
            name=migrated.get("name"),
            set_id=migrated.get("id"),
            set_type=set_type,
            folder_id=migrated.get("folder_id"),
            source=migrated.get("source"),
            output_directory=migrated.get("output_directory"),
            filename_template_id=migrated.get("filename_template_id"),
            persistent=migrated.get("persistent", True),
            publication_settings=migrated.get("publication_settings"),
            rule_definition=rule_definition,
            exclusions=migrated.get("exclusions", []),
            snapshot_key=migrated.get("snapshot_key"),
        )
        errors = result.validate()
        if errors:
            raise ValueError("Carnet invalide : {0}".format(", ".join(errors)))
        return result

    @classmethod
    def migrate(cls, data):
        """Retourne une copie normalisée vers le schéma courant."""
        version = data.get("schema_version", 0)
        if version > cls.CURRENT_VERSION:
            raise ValueError("Schéma de carnet non supporté : {0}".format(version))
        result = dict(data)
        if version == 0:
            # Schéma initial : un carnet sans type est considéré dynamique.
            result.setdefault("set_type", "dynamic")
            result.setdefault("persistent", True)
            result.setdefault("exclusions", [])
            result["schema_version"] = 1
        return result

    @staticmethod
    def _rule_definition_from_dict(data):
        if not isinstance(data, dict):
            raise ValueError("La définition des règles dynamiques est obligatoire.")
        root = DynamicPublicationSetSerializer._node_from_dict(data.get("root"))
        return DynamicRuleDefinition(
            root=root,
            exclusions=data.get("exclusions", []),
            name=data.get("name"),
        )

    @staticmethod
    def _node_from_dict(data):
        if not isinstance(data, dict):
            raise ValueError("Noeud de règle dynamique invalide.")
        node_type = data.get("type")
        if node_type == "rule":
            from models.dynamic_rule import DynamicRule
            return DynamicRule(
                field=data.get("field"),
                operator=data.get("operator", "equals"),
                value=data.get("value"),
                label=data.get("label"),
            )
        if node_type == "group":
            from models.dynamic_rule import DynamicRuleGroup
            return DynamicRuleGroup(
                logic=data.get("logic", "all"),
                children=[DynamicPublicationSetSerializer._node_from_dict(child)
                          for child in data.get("children", [])],
                label=data.get("label"),
            )
        raise ValueError("Type de noeud dynamique inconnu : {0}".format(node_type))
