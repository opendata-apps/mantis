with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    bun
    pnpm
    vite
  ];
  shellHook = ''
      mkdir -p .nix-node
      export BUN_PATH=$PWD/.nix-node
      export NPM_CONFIG_PREFIX=$PWD/.nix-node
      export PATH=$BUN_PATH/bin:$PATH
      export PATH=$BUN_PATH/bin:$PWD/node_modules/.bin:$PATH
  '';
}

