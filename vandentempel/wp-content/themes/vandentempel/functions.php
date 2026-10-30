<?php
/**
 * Vandentempel block theme.
 *
 * @package vandentempel
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'VANDENTEMPEL_VERSION', '1.0.0' );

add_action(
	'after_setup_theme',
	function () {
		add_theme_support( 'editor-styles' );
		add_editor_style( 'assets/css/theme.css' );
		add_theme_support( 'responsive-embeds' );
		add_theme_support( 'post-thumbnails' );
		add_post_type_support( 'page', 'excerpt' );
	}
);

add_action(
	'wp_enqueue_scripts',
	function () {
		wp_enqueue_style(
			'vandentempel',
			get_theme_file_uri( 'assets/css/theme.css' ),
			array(),
			VANDENTEMPEL_VERSION
		);
	}
);

add_action(
	'init',
	function () {
		register_block_pattern_category(
			'vandentempel',
			array( 'label' => __( 'Vandentempel', 'vandentempel' ) )
		);

		// Card style for groups, usable from the editor's Styles panel.
		register_block_style(
			'core/group',
			array(
				'name'  => 'vdt-card',
				'label' => __( 'Kaart', 'vandentempel' ),
			)
		);
		register_block_style(
			'core/button',
			array(
				'name'  => 'vdt-ghost',
				'label' => __( 'Omlijnd licht', 'vandentempel' ),
			)
		);
	}
);

/**
 * Shortcut to theme image URLs inside patterns.
 *
 * @param string $file File name in assets/images.
 */
function vandentempel_image( $file ) {
	return esc_url( get_theme_file_uri( 'assets/images/' . $file ) );
}
