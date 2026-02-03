with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    bun
    pnpm
    # vite is installed via bun/npm, not nix (nixpkgs "vite" is a different scientific tool)
  ];
  shellHook = ''
      mkdir -p .nix-node
      export BUN_PATH=$PWD/.nix-node
      export NPM_CONFIG_PREFIX=$PWD/.nix-node
      export PATH=$BUN_PATH/bin:$PATH
      export PATH=$BUN_PATH/bin:$PWD/node_modules/.bin:$PATH
  '';
}

