with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    bun
    just
    python313Packages.pytest_8_3
    python313Packages.ruff
    # vite is installed via bun/npm, not nix (nixpkgs "vite" is a different scientific tool)
  ];
  packages = with pkgs; [
    (python3.withPackages (ps: [ ps.flask ]))
    curl
    jq
  ];
  shellHook = ''
      mkdir -p .nix-node
      export BUN_PATH=$PWD/.nix-node
      export NPM_CONFIG_PREFIX=$PWD/.nix-node
      export PATH=$BUN_PATH/bin:$PATH
      export PATH=$BUN_PATH/bin:$PWD/node_modules/.bin:$PATH
  '';
}

