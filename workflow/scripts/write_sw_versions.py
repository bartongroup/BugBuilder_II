#!/usr/bin/env python

"""
Writes software versions to yaml file for multiqc report 

Required arguments:
    input: json file with software versions
    output: yaml file to write versions to
"""

import argparse
import json
import yaml

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Writes software versions to yaml file for multiqc report")
    parser.add_argument('--input', required=True, help='json file with software versions')
    parser.add_argument('--output', required=True, help='yaml file to write versions to')

    args = parser.parse_args()

    with open("workflow/config/config.yaml") as f:
        config = yaml.safe_load(f)
    containers = config.get('containers', {})

    print(f"Collecting software versions from file: {args.input}")

    with open(args.input) as f:
        db_versions = json.load(f)

    print("\nLoaded database versions:")
    for name, version in db_versions.items():
        print(f"  {name}: {version}")

    with open(args.output, 'w') as f:
        for name, container in containers.items():
            version = container.split(':')[-1].split('--')[0]

            db_version = None
            db_type = None

            if name in db_versions:
                db_version = db_versions[name].get('version')
                db_type = db_versions[name].get('type')

            if db_type is not None and db_version is not None:
                version += f" (database: {db_version} [{db_type}])"
            elif db_version is not None:
                    version += f" (database: {db_version})"

            f.write(f"{name}: '{version}'\n")