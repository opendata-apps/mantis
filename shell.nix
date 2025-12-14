with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    bun
    pnpm
  ];
  shellHook = ''
      mkdir -p .nix-node
      export BUN_PATH=$PWD/.nix-node
      export NPM_CONFIG_PREFIX=$PWD/.nix-node
      export PATH=$BUN_PATH/bin:$PATH
  '';
}

